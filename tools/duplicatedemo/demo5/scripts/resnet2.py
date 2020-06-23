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
from pathlib import Path
from os import listdir
import urllib
import time

from datetime import datetime
global circe_home_ip, circe_home_ip_port, taskname

taskname = Path(__file__).stem
resnet_task_num = int(taskname.split('resnet')[1])

global logging
logging.basicConfig(level = logging.DEBUG)
#Krishna

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC, SLEEP_TIME, STRAGGLER_THRESHOLD, CODING_PART1
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
SLEEP_TIME   = int(config['OTHER']['SLEEP_TIME'])
STRAGGLER_THRESHOLD   = float(config['OTHER']['STRAGGLER_THRESHOLD'])
CODING_PART1 = int(config['OTHER']['CODING_PART1'])

global global_info_ip, global_info_ip_port


def send_runtime_profile(msg):
    """
    Sending runtime profiling information to flask server on home

    Args:
        msg (str): the message to be sent

    Returns:
        str: the message if successful, "not ok" otherwise.

    Raises:
        Exception: if sending message to flask server on home is failed
    """
    try:
        logging.debug('Sending runtime stats')
        logging.debug(msg)
        circe_home_ip_port = os.environ['HOME_NODE'] + ":" + str(FLASK_SVC)
        url = "http://" + circe_home_ip_port + "/recv_runtime_profile"
        params = {'msg': msg, "work_node": taskname}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        logging.debug("Sending runtime profiling info to flask server on home FAILED!!!")
        logging.debug(e)
        return "not ok"
    return res

def send_runtime_stats(action, file_name,from_task):
    ts = time.time()
    new_file = os.path.split(file_name)[-1]
    original_name = new_file.split('.')[0]
    logging.debug(original_name)
    tmp_name = original_name.split('_')[-1]
    temp_name= tmp_name+'.JPEG'
    runtime_info = action +' '+ from_task+' '+ temp_name+ ' '+str(ts) 
    send_runtime_profile(runtime_info)

def task(file_, pathin, pathout):
    global resnet_task_num
    file_ = [file_] if isinstance(file_, str) else file_ 
    for f in file_:
        send_runtime_stats('rt_enter_task', f,'master')
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
        print(os.path.join(pathin, f))
        img = Image.open(os.path.join(pathin, f))

        ### Apply transforms.
       	img_tensor = composed(img)
        ### 3D -> 4D (batch dimension = 1)
        img_tensor.unsqueeze_(0) 
        #img_tensor =  input_batch[0]
        ### call the ResNet model
        try:
            print('Calling the resnet model')
            output = model(img_tensor) 
            pred = torch.argmax(output, dim=1).detach().numpy().tolist()
            ### To simulate slow downs
            # purposely add delay time to slow down the sending
            if (random.random() > STRAGGLER_THRESHOLD) and (taskname=='resnet0') :
                print(taskname)
                print("Sleeping")
                time.sleep(SLEEP_TIME) #>=2 
            ### Contact flask server
            f_stripped = f.split(".JPEG")[0]
            # job_id = int(f_stripped.split("_jobid_")[1])
            job_id = f_stripped.split('_')[-2]
            job_id = int(f_stripped.split('_')[-2].split('jobid')[1])
            print('job_id from the file is: ', job_id)
            print(job_id)

            ret_job_id = 0
            try:
                global_info_ip = os.environ['GLOBAL_IP']
                global_info_ip_port = global_info_ip + ":" + str(FLASK_SVC)
                if CODING_PART1:
                    ret_job_id = send_prediction_to_decoder_task(job_id, pred[0], global_info_ip_port)
            except Exception as e:
                print('Possibly running on the execution profiler')

            
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
                elif pred[0] == 270: ### white wolf. class 3
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass3_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 276: ### hyena. class 4
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass4_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 292: ### tiger. class 5
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass5_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 278: ### kitfox. class 5
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass6_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 283: ### persian cat. class 6
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass7_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 288: ### leopard. class 7
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass8_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 291: ### lion. class 8
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass9_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                
                elif pred[0] == 295: ### black bear. class 10
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass10_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 298: ### moongoose. class 11
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass11_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 340: ### zebra. class 12
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass12_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 341: ### hog. class 13
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass13_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 344: ### hippo. class 14
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass14_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 345: ### ox. class 15
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass15_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 346: ### buffallo. class 16
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass16_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 348: ### ram. class 17
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass17_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 352: ### impala . class 18
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass18_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 354: ### camel. class 19
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass19_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                elif pred[0] == 360: ### otter. class 20
                    source = os.path.join(pathin, f)
                    # f_split = f.split("prefix_")[1]
                    # destination = os.path.join(pathout, "class2_" + f)
                    destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass20_"+ f)
                    # destination = os.path.join(pathout, "storeclass2_" + f)
                    out_list.append(shutil.copyfile(source, destination))
                else: ### not either of the classes # do nothing
                    print('This does not belong to any classes!!!')
            else: # ret_job_id < 0
                print("The jobid %s has already been processed by the flask server" % (job_id))
                return [] #slow resnet node: return empty
        except Exception as e:
            print('This might be a black and white image')
            print(e)
            return []

    send_runtime_stats('rt_finish_task', out_list[0],'master')
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
    classlists = ['fireengine', 'schoolbus', 'whitewolf', 'hyena','tiger','kitfox', 'persiancat', 'leopard', 'lion',  'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
    classlist = classlists[0:5]
    num = 27
    filelist = []
    for i in classlist:
        for j in range(resnet_task_num+1,num+1,9):
            #filename = 'master_'+taskname+'_'+i+'_'+str(j)+'_jobid_0.JPEG'
            filename = 'master_'+taskname+'_jobid0_'+ str(j)+'img'+i+'.JPEG'
            filelist.append(filename)
    # outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    # filelist = [f for f in listdir(outpath) if f.startswith('master')]
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
