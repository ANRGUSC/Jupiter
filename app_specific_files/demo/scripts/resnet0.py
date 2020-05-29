import torch
from torchvision import models
from torchvision import transforms
import os
import numpy as np
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets
import shutil
import time
import configparser
import requests
import json
import random
#Krishna
import urllib
import logging
global logging
logging.basicConfig(level = logging.DEBUG)
#Krishna

resnet_task_num = 0

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC, SLEEP_TIME, STRAGGLER_THRESHOLD
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
SLEEP_TIME   = int(config['OTHER']['SLEEP_TIME'])
STRAGGLER_THRESHOLD   = float(config['OTHER']['STRAGGLER_THRESHOLD'])

global global_info_ip, global_info_ip_port

def task(file_, pathin, pathout):
    global resnet_task_num
    file_ = [file_] if isinstance(file_, str) else file_ 
    ### set device to CPU
    device = torch.device("cpu")
    ### Load model
    model = models.resnet34(pretrained=True)
    model.eval()
    model.to(device)
    ### Transforms to be applied on input images
    composed = transforms.Compose([
               transforms.Resize(256, Image.ANTIALIAS),
               transforms.CenterCrop(224),
               transforms.ToTensor()])
    out_list = []

    for i, f in enumerate(file_):
        ### Read input files.
        img = Image.open(os.path.join(pathin, f))

        ### Apply transforms.
       	img_tensor = composed(img)
        ### 3D -> 4D (batch dimension = 1)
        img_tensor.unsqueeze_(0) 
        #img_tensor =  input_batch[0]
        ### call the ResNet model
        try:
            output = model(img_tensor) 
            pred = torch.argmax(output, dim=1).detach().numpy().tolist()
            ### To simulate slow downs
            # purposely add delay time to slow down the sending
            if random.random() > STRAGGLER_THRESHOLD:
                print("Sleeping")
                time.sleep(SLEEP_TIME) #>=2 
            ### Contact flask server
            f_stripped = f.split(".JPEG")[0]
            job_id = int(f_stripped.split("_jobid_")[1])
            print('job_id from the file is: ', job_id)
            global_info_ip = os.environ['GLOBAL_IP']
            global_info_ip_port = global_info_ip + ":" + str(FLASK_SVC)
            ret_job_id = send_prediction_to_decoder_task(job_id, pred[0], global_info_ip_port)
            if ret_job_id >= 0: # This job_id has not been processed by the global flask server
                ### Copy to appropriate destination paths
                if pred[0] == 555: ### fire engine. class 1
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    #destination = os.path.join(pathout, "class1_" + f)
                    destination = os.path.join(pathout,  "resnet" + str(resnet_task_num)+ "_storeclass1_" + f)
                    # destination = os.path.join(pathout, "storeclass1_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 779: ### school bus. class 2
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass2_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                else: ### not either of the classes # do nothing
                    print('This does not belong to any classes!!!')
                    #source = os.path.join(pathin, f)
                    #destination = os.path.join(pathout, "classNA_" + f)
                    #out_list.append(shutil.copyfile(source, destination))
            else: # ret_job_id < 0
                print("The jobid %s has already been processed by the flask server" % (job_id))
                return [] #slow resnet node: return empty
        except Exception as e:
            logging.debug("Exception during Resnet prediction")
            logging.debug(e)

    return out_list

#Krishna
def send_prediction_to_decoder_task(job_id, prediction, global_info_ip_port):
    """
    Sending prediction and resnet node task's number to flask server on decoder
    Args:
        prediction: the prediction to be sent
    Returns:
        str: the message if successful, "not ok" otherwise.
    Raises:
        Exception: if sending message to flask server on decoder is failed
    """
    global resnet_task_num
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
#Krishna

def main():
    #filelist = ["master_resnet0_n03345487_10.JPEG"]
    filelist = ['master_resnet0_n03345487_10_jobid_0.JPEG','master_resnet0_n04146614_1_jobid_0.JPEG','master_resnet0_n04146614_25_jobid_0.JPEG','master_resnet0_n04146614_27_jobid_0.JPEG',
       'master_resnet0_n04146614_30_jobid_0.JPEG','master_resnet0_n04146614_36_jobid_0.JPEG',
       'master_resnet0_n03345487_351_jobid_0.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
