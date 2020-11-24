import os
import shutil
import sys
import queue
import threading
import logging
import glob
import time
import json

from PIL import Image
from multiprocessing import Process, Manager
from flask import Flask, request
import configparser
import urllib
import collections
import requests
import numpy as np
from ccdag_utils import *




logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

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

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)
app = Flask(__name__)
config = configparser.ConfigParser()
config.read(ccdag.JUPITER_CONFIG_INI_PATH)
ssh_svc_port, _ = config['PORT_MAPPINGS']['SSH'].split(':')
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])


global all_nodes, all_nodes_ips, map_nodes_ip, master_node_port
store_class_tasks_dict = {}
store_class_tasks_dict[555] = "storeclass1"
store_class_tasks_dict[779] = "storeclass2"
store_class_tasks_dict[270] = "storeclass3"
store_class_tasks_dict[292] = "storeclass4"
store_class_tasks_dict[278] = "storeclass5"
store_class_tasks_dict[283] = "storeclass6"
store_class_tasks_dict[288] = "storeclass7"
store_class_tasks_dict[298] = "storeclass8"
store_class_tasks_dict[295] = "storeclass9"
store_class_tasks_dict[340] = "storeclass10"
store_class_tasks_dict[344] = "storeclass11"
store_class_tasks_dict[346] = "storeclass12"
store_class_tasks_dict[348] = "storeclass13"
store_class_tasks_dict[352] = "storeclass14"
store_class_tasks_dict[354] = "storeclass15"
store_class_tasks_dict[360] = "storeclass16"
store_class_tasks_dict[345] = "storeclass17"
store_class_tasks_dict[291] = "storeclass18"
store_class_tasks_dict[341] = "storeclass19"
store_class_tasks_dict[276] = "storeclass20"

classids = np.arange(0,len(ccdag.classlist),1)
classmap = dict(zip(ccdag.classlist, classids))

store_list = ["storeclass%d"%(d) for d in range(1,20)]


def transfer_data_scp(ID,user,pword,source, destination):
    """Transfer data using SCP

    Args:
        ID (str): destination ID
        user (str): username
        pword (str): password
        source (str): source file path
        destination (str): destination file path
    """
    #Keep retrying in case the containers are still building/booting up on
    #the child nodes.
    retry = 0
    ts = -1
    num_retries = 30
    print('Transfering the image to the storeclass')
    nodeIP = retrieve_storeclass_info(os.environ['CIRCE_TASK_TO_IP'], ID)
    while retry < num_retries:
        try:
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_svc_port, source, user, nodeIP, destination)
            print(cmd)
            os.system(cmd)
            log.debug('data transfer complete\n')
            break
        except Exception as e:
            log.debug('SSH Connection refused or File transfer failed, will retry in 2 seconds')
            log.debug(e)
            time.sleep(2)
            retry += 1
    if retry == num_retries:
        print('Can not send the file to the storeclass')

def get_job_id():
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None #not using HTTP secure
                                }
    # message for requesting job_id
    payload = {}
    # address of flask server for class1 is 0.0.0.0:5000 and "post-id" is for requesting id
    try:
        # url = "http://0.0.0.0:5000/post-id"
        global_info_ip = retrieve_globalinfo(os.environ['CIRCE_NONDAG_TASK_TO_IP'])
        url = "http://%s:%s/post-id-master"%(global_info_ip,str(FLASK_SVC))
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        job_id = response.json()
    except Exception as e:
        log.debug('Possibly running on the execution profiler')
        job_id = 0
    return job_id

def put_filenames(job_id, filelist):
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None #not using HTTP secure
                                }
    # message for requesting job_id
    payload = {"job_id": job_id, "filelist":filelist}
    # address of flask server for class1 is 0.0.0.0:5000 and "post-id" is for requesting id
    try:
        # url = "http://0.0.0.0:5000/post-id"
        global_info_ip = retrieve_globalinfo(os.environ['CIRCE_NONDAG_TASK_TO_IP'])
        url = "http://%s:%s/post-files-master"%(global_info_ip,str(FLASK_SVC))
        # request job_id
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        next_job_id = response.json()
    except Exception as e:
        log.debug('Possibly running on the execution profiler')
        next_job_id = 1
    return next_job_id

#Krishna
def get_enough_resnet_preds(job_id, global_info_ip_port):
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None #not using HTTP secure
                                    }
    try:
        log.debug('get enough resnet predictions from the decoder')
        url = "http://" + global_info_ip_port + "/post-enough-resnet-preds"
        params = {"job_id": job_id}
        response = requests.post(url, headers = hdr, data = json.dumps(params))
        ret_val = response.json()
        log.debug(ret_val)
    except Exception as e:
        log.debug("Get enough resnet predictions FAILED!!! - possibly running on the execution profiler")
        #logging.debug(e)
        ret_val = True
    return ret_val

def get_and_send_missing_images(pathin):
    # Check with global info server
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None #not using HTTP secure
                                }
    # message for requesting job_id
    payload = {}
    try:
        # url = "http://0.0.0.0:5000/post-id"
        global_info_ip = retrieve_globalinfo(os.environ['CIRCE_NONDAG_TASK_TO_IP'])
        url = "http://%s:%s/post-get-images-master"%(global_info_ip,str(FLASK_SVC))
        # request job_id
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        missing_images_dict = response.json()
        log.debug('Get and send missing images')
        log.debug(missing_images_dict)
    except Exception as e:
        log.debug('Exception during post-get-images-master')
        log.debug(e)
        missing_images_dict = collections.defaultdict(list)
    # Process and send requests out
    ### Reusing the input files to the master node. NOT creating a local copy of input files.
    print('Receive missing from decoder task:')
    for image_file, _class in missing_images_dict.items():
        file_name= image_file.split('/')[-1].split('_')[-1]
        log.debug('Transfer the file')        
        try:
            next_store_class = store_class_tasks_dict[int(_class)]
            new_file = 'home_' + next_store_class+'_'+file_name
            destination_path = os.path.join('/jupiter/circe_input',new_file)
            if next_store_class in store_list:
                print('Transfer image directly from master node')
                transfer_data_scp(next_store_class,'root','PASSWORD',image_file, destination_path)
            else:
                print("Next store class is outside the list of current store classes")
        except Exception as e:
            log.debug('The predicted item is not available in the stored class')
    return "ok"
#KRishna

def create_collage(input_list, collage_spatial, single_spatial, single_spatial_full, w):
    collage = Image.new('RGB', (single_spatial*w,single_spatial*w))
    collage_resized = Image.new('RGB', (collage_spatial, collage_spatial))
    ### Crop boundaries. Square shaped.
    left_crop = (single_spatial_full - single_spatial)/2
    top_crop = (single_spatial_full - single_spatial)/2
    right_crop = (single_spatial_full + single_spatial)/2
    bottom_crop = (single_spatial_full + single_spatial)/2

    for j in range(w):
        for i in range(w):
            ### NOTE: Logic for creation of collage can be modified depending on latency requirements.
            ### open -> resize -> crop
            idx = j * w + i
            im = Image.open(input_list[idx]).resize((single_spatial_full,single_spatial_full), Image.ANTIALIAS).crop((left_crop, top_crop, right_crop, bottom_crop))
            ### insert into collage. append label.
            collage.paste(im, (int(i*single_spatial), int(j*single_spatial)))
    #collage = np.asarray(collage)
    #collage = np.transpose(collage,(2,0,1))
    #collage /= 255.0
    ### write to file
    collage_name = "collage.JPEG"
    collage_resized = collage.resize((collage_spatial, collage_spatial), Image.ANTIALIAS)
    collage_resized.save(collage_name)
    return collage_name




# Run by dispatcher (e.g. CIRCE). Use task_name to differentiate the tasks by
# name to reuse one base task file.
def task(q, pathin, pathout, task_name):
    children = app_config.child_tasks(task_name)

    while True:
        if q.qsize()>=9:
            input_list = []
            src_list = []
            base_list = []
            id_list = []
            for i in range(0,9): #number of inputs is 9
                input_file = q.get()
                show_run_stats(task_name,'queue_start_process',input_file)
                input_list.append(input_file)
                src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
                #show_run_stats(task_name,'queue_start_process',input_file,src_task)
                log.debug(f"{task_name}: file rcvd from {src_task} {base_fname}")
                src = os.path.join(pathin, input_file)
                src_list.append(src)
                base_list.append(base_fname.split('.')[0])
                id_list.append(base_fname.split('img')[0])
                


            # Process the file (this example just passes along the file as-is)
            # Once a file is copied to the `pathout` folder, CIRCE will inspect the
            # filename and pass the file to the next task.

            # dst_task = children[cnt % len(children)]  # round robin selection
            # dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
            # shutil.copyfile(src, dst)

            # MASTER CODE
            w = 3
            num_images = w * w
            collage_spatial = 416
            single_spatial = 224
            single_spatial_full = 256

            # get job id for this requests
            job_id = get_job_id()
            log.debug("got job id")
            log.debug(job_id)
            collage_file = create_collage(src_list, collage_spatial, single_spatial, single_spatial_full, w)
            collage_file_split = collage_file.split(".JPEG")[0]
            classname = [x.split('.')[0].split('img')[1] for x in base_list]
            classid = [classmap[x] for x in classname]
            filesuffixlist = []
            for x,y in zip(classid, id_list):
                tmp = str(x)+'#'+y
                filesuffixlist.append(tmp)
            filesuffix = '-'.join(filesuffixlist)
            job = "jobid"+ str(job_id)
            dst = os.path.join(pathout, f"{task_name}_{collage_file_split}_{filesuffix}{job}")
            shutil.copyfile(collage_file, dst)
            show_run_stats(task_name,'queue_end_process',f"{task_name}_{collage_file_split}_{filesuffix}{job}")
            #show_run_stats(task_name,'queue_end_process',f"{task_name}_{collage_file_split}_{filesuffix}{job}",src_task)
            log.debug('Receive collage file:')
            log.debug(dst)
            log.debug('Receive resnet file:')
            ### send to resnet tasks
            filelist_flask = []
            for i, f in enumerate(input_list):
                idx  = i%num_images
                dst_task = "resnet"+str(idx) # only 1 children
                dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_list[i]}{job}.JPEG")
                log.debug(dst)
                shutil.copyfile(os.path.join(pathin,f), dst)
                filelist_flask.append(dst)
                show_run_stats(task_name,'queue_end_process',f"{task_name}_{dst_task}_{base_list[i]}{job}.JPEG")
                #show_run_stats(task_name,'queue_end_process',f"{task_name}_{dst_task}_{base_list[i]}{job}.JPEG",src_task)
            next_job_id = put_filenames(job_id, filelist_flask)
            if ccdag.CODING_PART1:
                slept = 0
                try:
                    global_info_ip = retrieve_globalinfo(os.environ['CIRCE_NONDAG_TASK_TO_IP'])
                    global_info_ip_port = global_info_ip + ":" + str(FLASK_SVC)
                    if ccdag.RESNETS_THRESHOLD > 1: # Coding configuration
                        while slept < ccdag.MASTER_TO_RESNET_TIME:
                            ret_val = get_enough_resnet_preds(job_id, global_info_ip_port)
                            log.debug("get_enough_resnet_preds fn. return value is: ")
                            log.debug(ret_val)
                            if ret_val:
                                break
                            time.sleep(ccdag.MASTER_POLL_INTERVAL)
                            slept += ccdag.MASTER_POLL_INTERVAL
                    get_and_send_missing_images(pathin)
                except Exception as e:
                    log.debug('Possibly running on execution profiler!!!')

            # read the generate output
            # based on that determine sleep and number of bytes in output file
            
            for i in range(0,9):
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