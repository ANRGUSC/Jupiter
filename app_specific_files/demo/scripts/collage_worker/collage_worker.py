import torch
import torchvision.transforms as transforms
import numpy as np
import os.path
import json
from flask import Flask, jsonify, request
import socket
import struct
import fcntl
import requests

import argparse
import time
from models import Darknet
#from utils.datasets import *
from utils.utils import *
from utils import torch_utils
import math

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.Struct(b'256s').pack(ifname[:15].encode('utf-8'))
    )[20:24])

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

#def process_collage(pred, img_size, output_dir, save_txt):
def process_collage(pred):
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
 
# load model
#torch.cuda.empty_cache()
#device = torch.device("cuda:0")
device = torch.device("cpu")
img_size=416
w = 4
single_spatial = math.ceil(img_size*1.0/w)
nms_thres = 0.45
conf_thres = 0.3
net_config_path = "/home/collage_inference/collage_worker/cfg/yolov3-tiny.cfg"
classes_list = np.load("/home/collage_inference/collage_worker/classes_list_103_classes.npy")
classes_list = np.sort(classes_list)

model = Darknet(net_config_path, img_size)
weights_file_path = "/home/collage_inference/collage_worker/weights/best.pt"
#checkpoint = torch.load(weights_file_path, map_location="cuda:0")
checkpoint = torch.load(weights_file_path, map_location="cpu")
model.load_state_dict(checkpoint['model'])
del checkpoint
model.to(device).eval()

output_dir = "/home/collage_inference/collage_worker/collage_output/"
os.system('rm -rf ' + output_dir)
os.makedirs(output_dir, exist_ok=True)

distrib = np.load('/home/collage_inference/collage_worker/latency_distribution.npy')

app = Flask('Collage prediction serving app')
@app.route("/")
def hello():
    return "Collage classification using YOLOv3\n"

@app.route('/predict', methods=['POST'])
def predict():
    input = request.get_json()
    tensor = torch.tensor(input['image']).to(device)
    #target = torch.tensor(input['label']).to(device)
    img_detections = []  # Stores detections for each image index
    begin = time.time()
    pred = model(tensor)
    pred = pred.cpu()
    print('inference', time.time() - begin)
    decode_begin = time.time()
    final_preds = process_collage(pred)
    print('decode', time.time() - decode_begin)
    #torch.cuda.synchronize() 
    #final_preds = process_collage(pred, img_size, output_dir, save_txt=False)
    #print(pred.shape)
    now = time.time()-begin
    #a, m = 1.5, 0.1
    #s = (np.random.pareto(a) + 1) * m
    s = np.random.choice(distrib)
    #print (s, now)
    if now < s:
        time.sleep(s - now)
        latency = s
    else:
        latency = now
    #latency = now
    resp = {'latency': latency, 'pred': final_preds}
    return jsonify(resp) 

if __name__ == '__main__':
    hdr = {
    'Content-Type': 'application/json',
    'Authorization': None #not using HTTP secure
    }
    #json_dump = json.dumps({'ip': get_ip_address('eth0')})
    #resp = requests.post('http://elon.usc.edu:8882/ip', data = json_dump)
    app.run(host="0.0.0.0", debug=True)
