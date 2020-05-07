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
import grequests
import json
#import cv2
import sys

def compute_accuracy(pred, target):
    total = len(pred)
    pred = np.array(pred).reshape(-1, total)
    target = target.reshape(-1, total)
    su = np.sum(pred==target)
    return su, total

class TargetTransform(object):
    def __init__(self):
        self.classes_list = np.load("/home/collage_inference/master_service/classes_list_103_classes.npy")
        self.classes_list = np.sort(self.classes_list)
    def __call__(self, target):
        return self.classes_list[target]

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def merge_pil(input_batch, collage_spatial, single_spatial, single_spatial_full, w):
    collage = Image.new('RGB', (single_spatial*w,single_spatial*w))
    for j in range(w):
        for i in range(w):
            im = input_batch[j*w + i]
            #im = np.transpose(im, (1,2,0))
            im = Image.fromarray(im)
            collage.paste(im, (int(i*single_spatial), int(j*single_spatial)))
    
    #collage = collage.resize((collage_spatial, collage_spatial), Image.BILINEAR)
    collage = collage.resize((collage_spatial, collage_spatial), Image.ANTIALIAS)
    collage = np.asarray(collage)
    collage = np.transpose(collage,(2,0,1))
    return collage

def merge(input_batch, collage_spatial, single_spatial, w):
    cs = collage_spatial
    ss = single_spatial
    collage_arr = np.ones((ss*w, ss*w, 3))
    for j in range(w):
        for i in range(w):
            #print(input_batch.shape)
            collage_arr[int(j*ss):int((j+1)*ss), int(i*ss):int((i+1)*ss), :] = input_batch[j*w + i]
    #collage_arr = np.transpose(collage_arr, (1,2,0))
    collage_resized_arr = cv2.resize(collage_arr, dsize=(cs,cs), interpolation=cv2.INTER_LINEAR)
    collage_resized_arr = np.transpose(collage_resized_arr, (2,0,1))
    #print(collage_resized_arr.shape)
    return collage_resized_arr

def write_pred(batch_size, bi, preds, target, pred_file_name):
    line = '%d, ' % bi
    line += '{'
    for sample in range(0, batch_size - 1):
        line += str(target[sample][0]) + ', '
    line += str(target[batch_size - 1][0])
    line += '}'
    for i in range(0, batch_size+1):
        if i not in preds:
            line += 'NA, '
        else:
            if not i:
                line += str(preds[i]) + ', '
            else:
                line += str(preds[i][0]) + ', '

    with open(pred_file_name, 'a') as f:
        f.write(line + '\n')

# Read in images and infer
w = 3 
collage_spatial = 416
single_spatial = 224
single_spatial_full = 256
val_root = "/home/imagenet-data/raw-data/validation_100/"
#Crop boundaries. Square shaped.
left_crop = (single_spatial_full - single_spatial)/2
top_crop = (single_spatial_full - single_spatial)/2
right_crop = (single_spatial_full + single_spatial)/2
bottom_crop = (single_spatial_full + single_spatial)/2
#normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
#                                     std=[0.229, 0.224, 0.225])
composed = transforms.Compose([
            transforms.Resize(256, Image.ANTIALIAS),
#            transforms.Resize(256),
            transforms.CenterCrop(224),
#            transforms.ToTensorCollage()])
            transforms.ToTensor()])
#            normalize])
reverse_map = TargetTransform()
imagenet_val_data = datasets.ImageFolder(root=val_root, transform=composed, target_transform = reverse_map) ##Subset of imagenet classes
#imagenet_val_data = datasets.ImageFolder(root=val_root, target_transform = reverse_map) ##Subset of imagenet classes
servers = []
with open('./worker_ips', 'r') as f:
    for ip in f:
        ip = ip.strip()
        servers.append('http://%s:5000/predict' % ip)
batch_size = w*w
#print(servers)
correct_acc = total_acc = 0.0
epoch = 0
while True:
    avg_merge_time = 0.0
    num_batches = 0
    epoch += 1
    if epoch > 1: break
    end_to_end_file_name = 'collage_latency_result/end_to_end_epoch_%d' % epoch
    pred_file_name = 'collage_latency_result/predictions_epoch_%d' % epoch
    slow_node_file_name = 'collage_latency_result/slow_nodes_epoch_%d' % epoch
#if True:
    val_loader = DataLoader(imagenet_val_data, batch_size=batch_size, shuffle=False)
    hdr = {
        'Content-Type': 'application/json',
        'Authorization': None #not using HTTP secure
    }
    for bi, (input_batch, target) in enumerate(val_loader):
        input_batch = input_batch.numpy()
        input_batch_modified = np.zeros((input_batch.shape[0],input_batch.shape[3],input_batch.shape[1],input_batch.shape[2]))
        if(input_batch.shape[0] !=batch_size):
            continue
        #if num_batches >= 10:
        #    break
        num_batches += 1
        merge_begin = time.time()
        collage = merge_pil(input_batch, collage_spatial, single_spatial, single_spatial_full, w).astype(np.float16)
        #collage = merge(input_batch, collage_spatial, single_spatial, w).astype(np.float16)
        collage /= 255.0
        merge_time = time.time() - merge_begin
        num_batches += 1
        avg_merge_time += merge_time
        #continue
        #collage = merge(input_batch, collage_spatial, single_spatial, w)
        #print("time taken for merge is: ", (time.time()-merge_begin))
        #input_batch = input_batch.astype(np.float16)
        for b in range(batch_size):
            input_batch_modified[b] = np.transpose(input_batch[b], (2,0,1))
            input_batch_modified[b] /= 255.0
        
        input_batch_modified = input_batch_modified.astype(np.float16)
        target = target.numpy().reshape(batch_size, -1)
        json_dumps = []
        #print (input_batch[0].shape, input_batch[0].dtype)
        #print (collage.shape, collage.dtype)
        json_dumps.append(json.dumps({'image' : np.expand_dims(collage, axis=0)}, cls=NumpyEncoder))
        #for b in range(batch_size):
        for b in range(1):
            json_dumps.append(json.dumps({'image' : np.expand_dims(input_batch_modified[b], axis=0), 'label' : target[b]}, cls=NumpyEncoder))
 

        resp_begin = time.time()
        responses = (grequests.post(url, headers = hdr, data = json_dump, timeout=5.65) for (url, json_dump) in zip(servers, json_dumps))
        #responses = (grequests.post(url, headers = hdr, data = json_dump) for (url, json_dump) in zip(servers, json_dumps))
        #responses = grequests.imap(responses, size=5)
        responses = grequests.map(responses)
        #print('batch No.%d' % i)
        slow_servers = []
        preds = {}
        for i, response in enumerate(responses):
#            if response is None:
#                print('too slow')
#            else:
            if True:
                with open('collage_latency_result/vm%d' % i, 'a') as f:
                    if response is None:
                        print(servers[i] + ' is too slow\n')
                        f.write('12345\n')
                        slow_servers.append(i)
                    else:
                        #print(str(response.json()['pred'])+'\n')
                        #print(str(response.headers)+'\n')
                        #print("response of: is: ", i, response)
                        preds[i] = response.json()['pred']
                        f.write(str(response.json()['latency']) + '\n')
            
        # need to resubmit request if the collage model is also running slow   
        if len(slow_servers) > 0:
            with open(slow_node_file_name, 'a') as f:
                f.write('%d, %s\n' % (bi, slow_servers))
        if len(slow_servers) > 1 and 0 in slow_servers:
            # never resubmit collage request
            slow_servers.remove(0)
            fast_servers = list(range(1, len(servers)))
            for slow_server in slow_servers:
                fast_servers.remove(slow_server)
            fast_servers = np.random.choice(fast_servers, len(slow_servers))
            # do not put timeout for the replicate request
            print(fast_servers, slow_servers)
            responses = (grequests.post(servers[server_idx], headers = hdr, data = json_dumps[req_idx]) for server_idx, req_idx in zip(fast_servers, slow_servers))
            responses = grequests.map(responses)
            
            for i, response in enumerate(responses):
                preds[slow_servers[i]] = response.json()['pred']

        resp_time = time.time() - resp_begin
        write_pred(batch_size, bi, preds, target, pred_file_name)
        if 0 in preds:#collage node is not slow
            correct, total = compute_accuracy(preds[0], target)
            correct_acc += correct
            total_acc += total
        #print("accuracy is: {}%, {},{}".format(correct*100.0/total, correct, total))
        with open(end_to_end_file_name, 'a') as f:
            f.write('%d, %s, %s, %s\n' % (bi, str(resp_time + merge_time), str(resp_time), str(merge_time)))
        #if bi == 10:
        #    print("acc. accuracy is: {}%, {},{}".format(correct_acc*100.0/total_acc, correct_acc, total_acc))
        #    sys.exit(0)
    #print("Average time taken for merge is: ", avg_merge_time/num_batches)
    print("cumulative collage model accuracy is: {}%, {},{}".format(correct_acc*100.0/total_acc, correct_acc, total_acc))
