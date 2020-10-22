import os
import shutil
import sys
import queue
import threading
import logging
import glob
import time
import json
import numpy as np
import requests
import urllib
import configparser
import cv2
from ccdag_utils import *

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
    sys.path.append("/jupiter/build/app_specific_files/")
    from jupiter_utils import app_config_parser
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../core/")
    from jupiter_utils import app_config_parser

import ccdag

classids = np.arange(0,len(ccdag.classlist),1)
classmap = dict(zip(ccdag.classlist, classids))

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)

#task config information

config = configparser.ConfigParser()
config.read(ccdag.JUPITER_CONFIG_INI_PATH)

FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])

def gen_Lagrange_coeffs(alpha_s,beta_s):
    U = np.zeros((len(alpha_s), len(beta_s)))
    for i in range(len(alpha_s)):
        for j in range(len(beta_s)):
            cur_beta = beta_s[j];
            den = np.prod([cur_beta - o   for o in beta_s if cur_beta != o])
            num = np.prod([alpha_s[i] - o for o in beta_s if cur_beta != o])
            U[i][j] = num/den
    return U


def LCC_encoding(X,N,M):
    w,l = X[0].shape
    n_beta = M
    beta_s, alpha_s = range(1,1+n_beta), range(1+n_beta,N+1+n_beta)

    U = gen_Lagrange_coeffs(alpha_s,beta_s)
    X_LCC = []
    for i in range(N):
        X_zero = np.zeros(X[0].shape)
        for j in range(M):
            X_zero = X_zero + U[i][j]*X[j]
        X_LCC.append(X_zero)
    return X_LCC


# Run by dispatcher (e.g. CIRCE). Use task_name to differentiate the tasks by
# name to reuse one base task file.
def task(q, pathin, pathout, task_name):
    children = app_config.child_tasks(task_name)
    classnum = task_name.split('lccenc')[1]
    classname = ccdag.classlist[int(classnum)-1]
    # Parameters
    # L = 10 # Number of images in a data-batch
    L = 2 # Number of images in a data-batch
    M = 2 # Number of data-batches
    N = 3 # Number of workers (encoded data-batches)

    if ccdag.CODING_PART2==1:
        num_inputs = 4
    else:
        num_inputs = 6
    while True:
        if q.qsize()>=num_inputs:
            input_list = []
            src_list = []
            base_list = []
            id_list = []
            for i in range(0,num_inputs): #number of inputs is 9
                input_file = q.get()
                input_list.append(input_file)
                src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
                log.debug(f"{task_name}: file rcvd from {src_task} : {input_file}")
                src = os.path.join(pathin, input_file)
                src_list.append(src)
                base_list.append(base_fname.split('jobid')[0])
                id_list.append(base_fname.split('img')[0])

            start = time.time()


            #LCCENC CODE

            logging.debug(id_list)
            classname = [x.split('.')[0].split('img')[1] for x in base_list]
            classid = [classmap[x] for x in classname]
            filesuffixlist = []
            for x,y in zip(classid, id_list):
                tmp = str(x)+'#'+y
                filesuffixlist.append(tmp)
            filesuffix = '-'.join(filesuffixlist)
            logging.debug(filesuffix)

            hdr = {
                    'Content-Type': 'application/json',
                    'Authorization': None #not using HTTP secure
                                        }
            # message for requesting job_id
            # payload = {'event': 'request id'}
            payload = {'class_image': int(classnum)}
            # address of flask server for class1 is 0.0.0.0:5000 and "post-id" is for requesting id
            try:
                # url = "http://0.0.0.0:5000/post-id"
                global_info_ip = retrieve_globalinfo(os.environ['CIRCE_NONDAG_TASK_TO_IP'])
                url = "http://%s:%s/post-id"%(global_info_ip,str(FLASK_SVC))
                # request job_id

                response = requests.post(url, headers = hdr, data = json.dumps(payload))
                job_id = response.json()
            except Exception as e:
                log.debug('Possibly running on the execution profiler')
                log.debug(e)
                job_id = 2



            # Dimension of resized image
            width = 400
            height = 400
            dim = (width, height)

            if ccdag.CODING_PART2: #Coding Version
                #Read M batches
                Image_Batch = []
                count_file = 0
                for j in range(M):
                    count = 0
                    while count < L:
                        logging.debug(count_file)
                        logging.debug(os.path.join(pathin, input_list[count_file]))
                        img = cv2.imread(os.path.join(pathin, input_list[count_file]))
                        if img is not None:
                        # resize image
                            img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
                            img = np.float64(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
                            img -= img.mean()
                            img /= img.std()
                            img_w ,img_l = img.shape
                            img = img.reshape(1,img_w*img_l)
                            if count == 0:
                               Images = img
                            else:
                               Images = np.concatenate((Images,img), axis=0)
                            count+=1
                        count_file+=1
                    Image_Batch.append(Images)

                # Encode M data batches to N encoded data
                En_Image_Batch = LCC_encoding(Image_Batch,N,M)

                # Save each encoded data-batch i to a csv
                for idx,child in enumerate(children):
                    job = "jobid"+ str(job_id)
                    destination = os.path.join(pathout, f"{task_name}_{child}_{filesuffix}{job}.csv")
                    np.savetxt(destination, En_Image_Batch[idx], delimiter=',')

                from_task = '_storeclass'+classnum


            else: # Uncoding version
                #Read M batches
                Image_Batch = []
                count_file = 0
                for j in range(N):
                    count = 0
                    while count < L:
                        logging.debug(count_file)
                        img = cv2.imread(os.path.join(pathin, input_list[count_file]))
                        if img is not None:
                        # resize image
                            img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
                            img = np.float64(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
                            img -= img.mean()
                            img /= img.std()
                            img_w ,img_l = img.shape
                            img = img.reshape(1,img_w*img_l)
                            if count == 0:
                               Images = img
                            else:
                               Images = np.concatenate((Images,img), axis=0)
                            count+=1
                        count_file+=1
                    Image_Batch.append(Images)

                En_Image_Batch = LCC_encoding(Image_Batch,N,N)


                for idx,child in enumerate(children):
                    job = "jobid"+ str(job_id)
                    destination = os.path.join(pathout, f"{task_name}_{child}_{filesuffix}{job}.csv")
                    np.savetxt(destination, En_Image_Batch[idx], delimiter=',')

            # read the generate output
            # based on that determine sleep and number of bytes in output file
            end = time.time()
            runtime_stat = {
                "task_name" : task_name,
                "start" : start,
                "end" : end
            }
            log.info(f"runtime_stat:{json.dumps(runtime_stat)}")
            for i in range(num_inputs):
                q.task_done()
        else:
            log.debug('Not enough files')
            time.sleep(1)

    log.error("ERROR: should never reach this")


# Run by execution profiler
def profile_execution(task_name):
    q = queue.Queue()
    input_dir = f"{APP_DIR}/sample_inputs/"
    output_dir = f"{APP_DIR}/sample_outputs/"


    os.makedirs(output_dir, exist_ok=True)
    t = threading.Thread(target=task, args=(q, input_dir, output_dir, task_name))
    t.start()

    for file in os.listdir(input_dir):
        try:
            src_task, dst_task, base_fname = file.split("_", maxsplit=3)
        except ValueError:
            # file is not in the correct format
            continue

        if dst_task.startswith(task_name):
            q.put(file)
    q.join()


    # execution profiler needs the name of ouput files to analyze sizes
    output_files = []
    for file in os.listdir(output_dir):
        if file.startswith(task_name):
            output_files.append(file)

    return output_dir, output_files


if __name__ == '__main__':
    # Testing Only
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    for dag_task in app_config.get_dag_tasks():
        if dag_task['base_script'] == __file__:
            log.debug(profile_execution(dag_task['name']))