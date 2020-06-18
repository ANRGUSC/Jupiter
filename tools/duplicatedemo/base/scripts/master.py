# Bunch of import statements
import os
import shutil
from PIL import Image
# import numpy as np
#KRishna
from multiprocessing import Process, Manager
from flask import Flask, request
import configparser
import urllib
import logging
import time
import multiprocessing
from multiprocessing import Process, Manager
import collections
from os import listdir
import requests
import json

from pathlib import Path
from datetime import datetime
global circe_home_ip, circe_home_ip_port, taskname
taskname = Path(__file__).stem

#Krishna

"""
Task for master encoder node.
1) Takes as input multiple image files and creates a collage image file. It is ideal to have 9 different inputs to create one collage image. 
2) Sends the image files to ResNet or Collage task folders downstream.
"""
### create a collage image and write to a file

#KRishna
app = Flask(__name__)
global logging
logging.basicConfig(level = logging.DEBUG)
### NOTETOQUYNH: Need to set the below
### store class node tasks ip/port, store class node paths

store_class_tasks_paths_dict = {}

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC, num_retries, ssh_port, username, password, CODING_PART1
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
ssh_port    = int(config['PORT']['SSH_SVC'])
username    = config['AUTH']['USERNAME']
password    = config['AUTH']['PASSWORD']
CODING_PART1 = int(config['OTHER']['CODING_PART1'])

global all_nodes, all_nodes_ips, map_nodes_ip, master_node_port
all_nodes = os.environ["ALL_NODES"].split(":")
all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":") 
logging.debug(all_nodes)
map_nodes_ip = dict(zip(all_nodes, all_nodes_ips))
store_class_list = ['storeclass1','storeclass2']

global global_info_ip, global_info_ip_port



store_class_tasks_dict = {}
store_class_tasks_dict[555] = "storeclass1"
store_class_tasks_dict[779] = "storeclass2"
store_class_tasks_dict[270] = "storeclass3"
store_class_tasks_dict[276] = "storeclass4"
store_class_tasks_dict[278] = "storeclass5"
store_class_tasks_dict[283] = "storeclass6"
store_class_tasks_dict[288] = "storeclass7"
store_class_tasks_dict[291] = "storeclass8"
store_class_tasks_dict[292] = "storeclass9"
store_class_tasks_dict[295] = "storeclass10"
store_class_tasks_dict[298] = "storeclass11"
store_class_tasks_dict[340] = "storeclass12"
store_class_tasks_dict[341] = "storeclass13"
store_class_tasks_dict[344] = "storeclass14"
store_class_tasks_dict[345] = "storeclass15"
store_class_tasks_dict[346] = "storeclass16"
store_class_tasks_dict[348] = "storeclass17"
store_class_tasks_dict[352] = "storeclass18"
store_class_tasks_dict[354] = "storeclass19"
store_class_tasks_dict[360] = "storeclass20"


def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

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

def send_runtime_stats(action, file_names):
    t = datetime.now()
    ts = unix_time(t)
    for i in range(0,len(file_names)):
        file_name = file_names[i]
        new_file = os.path.split(file_name)[-1]
        original_name = new_file.split('.')[0]
        logging.debug(original_name)
        tmp_name = original_name.split('_')[-1]
        temp_name= tmp_name+'.JPEG'
        runtime_info = action +' '+ temp_name+ ' '+str(ts)
        send_runtime_profile(runtime_info)


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
    while retry < num_retries:
        try:
            logging.debug(map_nodes_ip)
            nodeIP = map_nodes_ip[ID]
            logging.debug(nodeIP)
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, nodeIP, destination)
            logging.debug(cmd)
            os.system(cmd)
            logging.debug('data transfer complete\n')
            break
        except Exception as e:
            logging.debug('SSH Connection refused or File transfer failed, will retry in 2 seconds')
            logging.debug(e)
            time.sleep(2)
            retry += 1
    if retry == num_retries:
        s = "{:<10} {:<10} {:<10} {:<10} \n".format(node_name,transfer_type,source,ts)
        runtime_sender_log.write(s)
        runtime_sender_log.flush()

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
        global_info_ip = os.environ['GLOBAL_IP']
        url = "http://%s:%s/post-id-master"%(global_info_ip,str(FLASK_SVC))
        print(url)
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        job_id = response.json()
        #print(job_id)
    except Exception as e:
        print('Possibly running on the execution profiler')
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
        global_info_ip = os.environ['GLOBAL_IP']
        url = "http://%s:%s/post-files-master"%(global_info_ip,str(FLASK_SVC))
        print(url)
        # request job_id
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        next_job_id = response.json()
    except Exception as e:
        print('Possibly running on the execution profiler')
        next_job_id = 1
    return next_job_id

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
        global_info_ip = os.environ['GLOBAL_IP']
        url = "http://%s:%s/post-get-images-master"%(global_info_ip,str(FLASK_SVC))
        print(url)
        # request job_id
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        missing_images_dict = response.json()
        print(missing_images_dict)
    except Exception as e:
        print('Possibly running on the execution profiler')
        logging.debug('Exception during post-get-images-master')
        logging.debug(e)
        missing_images_dict = collections.defaultdict(list)
    # Process and send requests out     
    ### Reusing the input files to the master node. NOT creating a local copy of input files.
    logging.debug('Receive missing from decoder task:')
    logging.debug(missing_images_dict)
    for image_file, _class in missing_images_dict.items(): 
        logging.debug(image_file)
        file_name_wo_jobid = image_file.split("_")[1]
        source_path = os.path.join(pathin, file_name_wo_jobid)
        file_name = 'master_master_master_master_' + image_file
        logging.debug('Transfer the file')
        destination_path = os.path.join('/centralized_scheduler/input',file_name)
        logging.debug(destination_path)
        try:
            next_store_class = store_class_tasks_dict[int(_class)]
            logging.debug(next_store_class)
            transfer_data_scp(next_store_class,username,password,source_path, destination_path)
        except Exception as e:
            logging.debug('The predicted item is not available in the stored class')
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
    print('New collage file is created!')
    print(collage_name)
    return collage_name

def task(filelist, pathin, pathout):
    out_list = []# output file list. Ordered as => [collage_file, image1, image2, ...., image9]
    ### send to collage task
    ### Collage image is arranged as a rectangular grid of shape w x w 
    filelist = [filelist] if isinstance(filelist, str) else filelist  

    send_runtime_stats('rt_enter_task', filelist)
    w = 3 
    num_images = w * w
    collage_spatial = 416
    single_spatial = 224
    single_spatial_full = 256
    input_list = []
    ### List of images that are used to create a collage image
    
    for i in range(num_images):
        ### Number of files in file list can be less than the number of images needed (9)
        file_idx = int(i % len(filelist))
        input_list.append(os.path.join(pathin, filelist[file_idx]))
        # KRishna
    print('Input list')
    print(input_list)
    # get job id for this requests
    job_id = get_job_id()
    logging.debug("got job id") 
    logging.debug(job_id) 
    print('got job id: ', job_id)
    collage_file = create_collage(input_list, collage_spatial, single_spatial, single_spatial_full, w)
    collage_file_split = collage_file.split(".JPEG")[0] 


    # fileid = [x.split('/')[-1].split('img')[0] for x in input_list]
    # classname = input_list[0].split('/')[-1].split('.')[0].split('img')[1]
    # filesuffix = classname+'-'+'-'.join(fileid)
    # logging.debug(filesuffix)


    shutil.copyfile(collage_file, os.path.join(pathout,"master_"+  collage_file_split + "_jobid" + str(job_id) + ".JPEG"))
    print('Receive collage file:')
    ### send to collage task
    outlist = [os.path.join(pathout,"master_"+  collage_file_split+ "_jobid" + str(job_id) + ".JPEG")]
    print(outlist)
    ### send to resnet tasks
    print('Receive resnet files: ')
    filelist_flask = []
    for i, f in enumerate(filelist):
        idx  = i%num_images
        f_split = f.split(".JPEG")[0]
        print('got job id 2: ', job_id)
        f_new = "jobid"+ str(job_id) + '_'+ f_split +  ".JPEG" 
        shutil.copyfile(os.path.join(pathin,f), os.path.join(pathout,"master_resnet"+str(idx)+'_'+ f_new))
        filelist_flask.append(f_new)
        outlist.append(os.path.join(pathout,"master_resnet"+str(idx)+'_'+f_new))
        print(outlist)
    next_job_id = put_filenames(job_id, filelist_flask)
    if CODING_PART1:
        get_and_send_missing_images(pathin) 

    send_runtime_stats('rt_finish_task', outlist)
    return outlist

def main():
    classlists = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard',  'lion', 'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
    classlist = classlists[0:5]
    logging.debug(classlist)
    num = 27
    filelist = []
    for i in classlist:
        for j in range(1,num+1):
            filename = str(j)+'img'+i+'.JPEG'
            #filename = i+'_'+str(j)+'.JPEG'
            filelist.append(filename)
    logging.debug(filelist)
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile



