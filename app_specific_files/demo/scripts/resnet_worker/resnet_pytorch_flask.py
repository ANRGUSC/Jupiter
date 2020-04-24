import torch
import torchvision.models as models
import torchvision.transforms as transforms
from skimage import io
import os
import pandas as pd
import numpy as np
from PIL import Image
import os.path
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets
import time
import json
from flask import Flask, jsonify, request
import socket
import struct
import fcntl
import requests

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.Struct(b'256s').pack(ifname[:15].encode('utf-8'))
    )[20:24])

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def compute_accuracy(output, target):
    pred = torch.argmax(output, dim=1)
    print("output: ", pred)
    print("target: ", target)
    su = torch.sum(pred==target).double()
    tot = target.shape[0]
    return su, tot

 
#device
device = torch.device("cpu")
#device = torch.device("cuda:0")
#Load model
model = models.resnet34(pretrained=True)
model.eval()
model.to(device)
distrib = np.load('/home/collage_inference/resnet/latency_distribution.npy')

#batch_time = AverageMeter()

app = Flask('resnet34 serving app')
@app.route("/")
def hello():
    return "Image classification using resnet34\n"

@app.route('/predict', methods=['POST'])
def predict():
    input = request.get_json()
    tensor = torch.tensor(input['image']).to(device)
    target = torch.tensor(input['label']).to(device)
    end = time.time()
    #print(tensor.shape)
    output = model(tensor) 
    pred = torch.argmax(output, dim=1).cpu().numpy().tolist()
    now = time.time() - end
    print('inference', now)
    #a, m = 1.5, 0.1
    #s = (np.random.pareto(a) + 1) * m
    s = np.random.choice(distrib)
    ##print (s, now)
    if now < s:
        time.sleep(s - now)
        latency = s
    else:
        latency = now
    #latency = now
    su, tot = compute_accuracy(output, target)
    #time.sleep(0.25)
    resp = {'pred': pred, 'latency': latency}
    return jsonify(resp) 

if __name__ == '__main__':
    hdr = {
    'Content-Type': 'application/json',
    'Authorization': None #not using HTTP secure
    }
    #json_dump = json.dumps({'ip': get_ip_address('eth0')})
    #json_dump = json.dumps({'ip': get_ip_address('ens5')})
    #resp = requests.post('http://elon.usc.edu:8882/ip', data = json_dump)
    app.run(host="0.0.0.0", debug=True)

