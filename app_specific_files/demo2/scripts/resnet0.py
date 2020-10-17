import os
import shutil
import sys
import queue
import threading
import logging
import glob
import time
import json

#task library import
import torch
from torchvision import models
from torchvision import transforms
from PIL import Image
import configparser
import requests
import random
from pathlib import Path
global circe_home_ip, circe_home_ip_port, taskname
taskname = Path(__file__).stem


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
    sys.path.append("../../mulhome_scripts/")
    from jupiter_utils import app_config_parser

import ccdag

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR, "demo5")

#task config information

config = configparser.ConfigParser()
config.read(ccdag.JUPITER_CONFIG_INI_PATH)

print(config.sections())
import os.path
if os.path.isfile(ccdag.JUPITER_CONFIG_INI_PATH):
    print('File found')
else:
    print('File not found')
global FLASK_DOCKER, FLASK_SVC
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
global global_info_ip, global_info_ip_port

#Krishna
def get_enough_resnet_preds(job_id, global_info_ip_port):
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None #not using HTTP secure
                                    }
    try:
        logging.debug('get enough resnet predictions from the decoder')
        url = "http://" + global_info_ip_port + "/post-enough-resnet-preds"
        params = {"job_id": job_id}
        response = requests.post(url, headers = hdr, data = json.dumps(params))
        ret_val = response.json()
        logging.debug(ret_val)
    except Exception as e:
        logging.debug("Get enough resnet predictions FAILED!!! - possibly running on the execution profiler")
        #logging.debug(e)
        ret_val = True
    return ret_val

#Krishna
def send_prediction_to_decoder_task(resnet_task_num,job_id, prediction, global_info_ip_port):
    """
    Sending prediction and resnet node task's number to flask server on decoder
    Args:
        prediction: the prediction to be sent
    Returns:
        str: the message if successful, "not ok" otherwise.
    Raises:
        Exception: if sending message to flask server on decoder is failed
    """
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None #not using HTTP secure
                                    }
    try:
        logging.debug('Send prediction to the decoder')
        url = "http://" + global_info_ip_port + "/post-prediction-resnet"
        params = {"job_id": job_id, 'msg': prediction, "resnet_task_num": resnet_task_num}
        response = requests.post(url, headers = hdr, data = json.dumps(params))
        ret_job_id = response.json()
        logging.debug(ret_job_id)
    except Exception as e:
        logging.debug("Sending my prediction info to flask server on decoder FAILED!!! - possibly running on the execution profiler")
        #logging.debug(e)
        ret_job_id = 0
    return ret_job_id

# Run by dispatcher (e.g. CIRCE). Use task_name to differentiate the tasks by
# name to reuse one base task file.
def task(q, pathin, pathout, task_name):
    resnet_task_num = int(task_name.split('resnet')[1])
    children = app_config.child_tasks(task_name)

    while True:
        input_file = q.get()
        src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
        log.info(f"{task_name}: file rcvd from {src_task}: {input_file}")

        # Process the file (this example just passes along the file as-is)
        # Once a file is copied to the `pathout` folder, CIRCE will inspect the
        # filename and pass the file to the next task.
        src = os.path.join(pathin, input_file)
        start = time.time()
        

        # RESNET CODE
        ### set device to CPU
        device = torch.device("cpu")
        print(device)
        ### Load model
        model = models.resnet34(pretrained=True)
        model.eval()
        model.to(device)
        print(model)
        ### Transforms to be applied on input images
        composed = transforms.Compose([
                   transforms.Resize(256, Image.ANTIALIAS),
                   transforms.CenterCrop(224),
                   transforms.ToTensor()])

        print(composed)

        ### Read input files.
        img = Image.open(src)
        print(img)

        ### Apply transforms.
        img_tensor = composed(img)
        ### 3D -> 4D (batch dimension = 1)
        img_tensor.unsqueeze_(0) 
        ### call the ResNet model
        try:
            print('Calling the resnet model')
            output = model(img_tensor) 
            pred = torch.argmax(output, dim=1).detach().numpy().tolist()
            ### To simulate slow downs
            # purposely add delay time to slow down the sending
            if (random.random() > ccdag.STRAGGLER_THRESHOLD) and (taskname=='resnet8') :
                print(taskname)
                print("Sleeping")
                time.sleep(ccdag.SLEEP_TIME) #>=2 
            ### Contact flask server
            f_stripped = input_file.split(".JPEG")[0]
            job_id = int(f_stripped.split('jobid')[1])
            print('job_id from the file is: ', job_id)

            ret_job_id = 0
            try:
                global_info_ip = os.environ['GLOBAL_IP']
                global_info_ip_port = global_info_ip + ":" + str(FLASK_SVC)
                if ccdag.CODING_PART1:
                    ret_job_id = send_prediction_to_decoder_task(resnet_task_num,job_id, pred[0], global_info_ip_port)
            except Exception as e:
                print('Possibly running on the execution profiler')

            try:
                global_info_ip = os.environ['GLOBAL_IP']
                global_info_ip_port = global_info_ip + ":" + str(FLASK_SVC)
                if taskname != 'resnet8':
                    slept = 0
                    while slept < ccdag.SLEEP_TIME:
                        ret_val = get_enough_resnet_preds(job_id, global_info_ip_port)
                        print("get_enough_resnet_preds fn. return value is: ", ret_val)
                        if ret_val:
                            break
                        time.sleep(ccdag.RESNET_POLL_INTERVAL)
                        slept += ccdag.RESNET_POLL_INTERVAL
            except Exception as e:
                print('Possibly running on the execution profiler, get_enough_resnet_preds')
            
            if ret_job_id >= 0: # This job_id has not been processed by the global flask server
                ### Copy to appropriate destination paths
                if pred[0] == 555: ### fire engine. class 1
                    print('Fireengine')
                    dst_task = 'storeclass1'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 779: ### school bus. class 2
                    print('Schoolbus')
                    dst_task = 'storeclass2'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 270: ### white wolf. class 3
                    print('White wolf')
                    dst_task = 'storeclass3'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 276: ### hyena. class 4
                    print('Hyena')
                    dst_task = 'storeclass4'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 292: ### tiger. class 5
                    print('Tiger')
                    dst_task = 'storeclass5'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 278: ### kitfox. class 5
                    print('Kitfox')
                    dst_task = 'storeclass6'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 283: ### persian cat. class 6
                    print('Persian cat')
                    dst_task = 'storeclass7'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 288: ### leopard. class 7
                    print('Leopard')
                    dst_task = 'storeclass8'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 291: ### lion. class 8
                    print('Lion')
                    dst_task = 'storeclass9'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 295: ### black bear. class 10
                    print('Black bear')
                    dst_task = 'storeclass10'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 298: ### moongoose. class 11
                    print('Goose')
                    dst_task = 'storeclass11'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 340: ### zebra. class 12
                    print('Zebra')
                    dst_task = 'storeclass12'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    print(dst)
                    shutil.copyfile(src, dst)
                elif pred[0] == 341: ### hog. class 13
                    print('Hog')
                    dst_task = 'storeclass13'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 344: ### hippo. class 14
                    print('Hippo')
                    dst_task = 'storeclass14'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 345: ### ox. class 15
                    print('Ox')
                    dst_task = 'storeclass15'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 346: ### buffallo. class 16
                    print('Buffallo')
                    dst_task = 'storeclass16'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 348: ### ram. class 17
                    print('Ram')
                    dst_task = 'storeclass17'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 352: ### impala . class 18
                    print('Impala')
                    dst_task = 'storeclass18'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 354: ### camel. class 19
                    print('Camel')
                    dst_task = 'storeclass19'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                elif pred[0] == 360: ### otter. class 20
                    print('Otters')
                    dst_task = 'storeclass20'
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                    shutil.copyfile(src, dst)
                else: ### not either of the classes # do nothing
                    print('This does not belong to any classes!!!')
                    print(pred[0])
                
            else: # ret_job_id < 0
                print("The jobid %s has already been processed by the flask server" % (job_id))
        except Exception as e:
            print('This might be a black and white image')
            print(e)


        # read the generate output
        # based on that determine sleep and number of bytes in output file
        end = time.time()
        runtime_stat = {
            "task_name" : task_name,
            "start" : start,
            "end" : end
        }
        log.warning(json.dumps(runtime_stat))
        # q.task_done()

    log.error("ERROR: should never reach this")


# Run by execution profiler
def profile_execution(task_name):
    q = queue.Queue()
    input_dir = f"{APP_DIR}/sample_inputs/"
    output_dir = f"{APP_DIR}/sample_outputs/"

    os.makedirs(output_dir, exist_ok=True)
    t = threading.Thread(target=task, args=(q, input_dir, output_dir, task_name))
    t.start()

    # for file in os.listdir(input_dir):
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

