import torch
from torchvision import transforms
# import torchvision.transforms as transforms
import numpy as np
import os
import math
from PIL import Image
from darknet_models import Darknet
from utils.utils import *
from utils import torch_utils
import pickle
import requests
import json
import configparser
import logging
import urllib
from os import listdir
import time

from pathlib import Path
from datetime import datetime
global circe_home_ip, circe_home_ip_port, taskname
taskname = Path(__file__).stem


global logging
logging.basicConfig(level = logging.DEBUG)

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC, CODING_PART1
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
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

def calculate_iou(L1, R1, T1, B1, L2, R2, T2, B2):
    L = max(L1, L2)
    R = min(R1, R2)    
    T = max(T1, T2)
    B = min(B1, B2)
    i = max(0, R-L+1) * max(0, B-T+1) #max(0,) covers the case where no intersection exists. Why +1 I am not sure
    A1 = (R1-L1+1) * (B1-T1+1)
    A2 = (R2-L2+1) * (B2-T2+1)
    iou = i*1.0/(A1 + A2 - i) 
    return iou
	
def calculate_pos(left, right, top, bottom, w, spatial):
    # return box in pos with maximum iou.
    pos_dict = {}
    for i in range(0,w):
        pos_dict[i] = [0]*w
        for j in range(0,w):
            pos_dict[i][j] = i + w*j
    max_iou = 0.0
    for i in range(w):
        t = i*spatial
        b = ((i+1)*spatial) - 1
        for j in range(w):
             l = j*spatial
             r = ((j+1)*spatial) - 1
             temp = calculate_iou(left, right, top, bottom, l, r, t, b)   
             if max_iou < temp:
                 max_iou = temp
                 x = j
                 y = i 
    #print(left, right, top, bottom, x, y)
    return (pos_dict[x])[y]
	
def process_collage(pred, nms_thres, conf_thres, classes_list, w, single_spatial):
    #print("pred1: ", pred.shape)
    pred = pred[pred[:, :, 4] > conf_thres]
    #print("pred2: ", pred.shape)
    if len(pred) > 0:
        detections_list = non_max_suppression(pred.unsqueeze(0), conf_thres, nms_thres)
        detections = detections_list[0]
        #print(len(detections_list)) 
        #print(detections.shape) 
    # Draw bounding boxes and labels of detections
    if detections is not None:
        # write results to .txt file
        #results_txt_path = output_dir + "/" + 'collage_preds.txt'
        #if os.path.isfile(results_txt_path):
        #    os.remove(results_txt_path)
        #print("detections info as follows:")
        #print(detections)
        predictions_prob_list = [-1]*w*w
        predictions_list = [-1]*w*w
        for x1, y1, x2, y2, conf, cls_conf, cls_pred in detections:
            #if save_txt:
            #    with open(results_txt_path, 'a') as file:
            #        file.write(('%g %g %g %g %g %g \n') % (x1, y1, x2, y2, cls_pred, cls_conf * conf))
            pos = calculate_pos(x1, x2, y1, y2, w, single_spatial)
            prob = cls_conf * conf
            cls_pred = int(cls_pred.item())
            #print("position and probability are: ", pos, prob)
            if predictions_prob_list[pos] != -1:
                if predictions_prob_list[pos] < prob:
                    predictions_list[pos] = cls_pred
            else:
                predictions_list[pos] = cls_pred
                predictions_prob_list[pos] = prob
    #print("predictions_list is: ", predictions_list)
    #predictions_arr = np.array(predictions_list)
    predictions_list = classes_list[predictions_list].tolist()
    return predictions_list
	
def task(file_, pathin, pathout):
    file_ = [file_] if isinstance(file_, str) else file_

    filesuffix = file_[0].split('.')[0].split('_')[-1]
    logging.debug(filesuffix)

    for f in file_:
        send_runtime_stats('rt_enter_task', f,'master')

    img_size=416
    w = 3
    single_spatial = math.ceil(img_size*1.0/w)
    nms_thres = 0.45
    conf_thres = 0.3
    # Load collage model
    device = torch.device("cpu")
    # net_config_path = "../collage_worker/cfg/yolov3-tiny.cfg"
    # net_config_path = "collage_worker/cfg/yolov3-tiny.cfg"
    net_config_path = os.path.join(os.path.dirname(__file__),"yolov3-tiny.cfg")
    model = Darknet(net_config_path, img_size)
    # weights_file_path = "../collage_worker/weights/best.pt"
    # weights_file_path = "collage_worker/weights/best.pt"
    weights_file_path = os.path.join(os.path.dirname(__file__),"best.pt")
    checkpoint = torch.load(weights_file_path, map_location="cpu")
    model.load_state_dict(checkpoint['model'])
    del checkpoint
    model.to(device).eval()
    # classes_list = np.load("./classes_list_103_classes.npy")
    classes_list = np.load(os.path.join(os.path.dirname(__file__),"classes_list_103_classes.npy"))
    classes_list = np.sort(classes_list)
    ### Load collage image
    composed = transforms.Compose([
               transforms.ToTensor()])
    for i, f in enumerate(file_):
        ### Read input files.
        collage_img = Image.open(os.path.join(pathin, f))
        ### Transform to tensor format.
        collage_tensor = composed(collage_img)
        ### 3D -> 4D (batch dimension = 1)
        collage_tensor.unsqueeze_(0) 
        ### Classify the image
        pred = model(collage_tensor)
        ### Process predictions	to get a list of final predictions
        final_preds = process_collage(pred, nms_thres, conf_thres, classes_list, w, single_spatial)
    ### Write predictions to a file and send it to decoder task's folder
        f_stripped = f.split(".JPEG")[0]
        job_id = int(f_stripped.split('_')[-2].split("jobid")[1])
        try:
            global_info_ip = os.environ['GLOBAL_IP']
            global_info_ip_port = global_info_ip + ":" + str(FLASK_SVC)
            print("global info ip port: ", global_info_ip_port)
            if CODING_PART1:
                send_prediction_to_decoder_task(job_id, final_preds, global_info_ip_port)
        except Exception as e:
            print('Possibly running on the execution profiler: ', e)
    out_list = []
    out_name = pathout + "collage"+'_'+filesuffix+".txt"
    with open(out_name, "w") as out_file:
        out_list.append(out_name)
        out_file.write("dummy output file")
        send_runtime_stats('rt_finish_task', out_name,'master')
        
    
    
    return out_list

#Krishna
def send_prediction_to_decoder_task(job_id, final_preds, global_info_ip_port):
    try:
        hdr = {
                'Content-Type': 'application/json',
                'Authorization': None #not using HTTP secure
                                        }
        logging.debug('Send prediction to the decoder')
        url = "http://" + global_info_ip_port + "/post-predictions-collage"
        logging.debug(url)
        params = {"job_id": job_id, 'msg': final_preds}
        response = requests.post(url, headers = hdr, data = json.dumps(params))
        logging.debug(response)
        ret_job_id = response.json()
        logging.debug(ret_job_id)
    except Exception as e:
        logging.debug("Sending my prediction info to flask server on decoder FAILED!!! - possibly running on the execution profiler")
        logging.debug(e)
        return "not ok"
    return "ok"

def main():
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    filelist = [f for f in listdir(outpath) if f.startswith('master_collage')]
    outfile = task(filelist, outpath, outpath)
    return outfile

