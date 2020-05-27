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

import requests
import json
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

global FLASK_DOCKER, FLASK_SVC, num_retries, ssh_port, username, password
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
ssh_port    = int(config['PORT']['SSH_SVC'])
username    = config['AUTH']['USERNAME']
password    = config['AUTH']['PASSWORD']

global all_nodes, all_nodes_ips, map_nodes_ip, master_node_port
all_nodes = os.environ["ALL_NODES"].split(":")
all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":") 
logging.debug(all_nodes)
map_nodes_ip = dict(zip(all_nodes, all_nodes_ips))
store_class_list = ['storeclass1','storeclass2']

global global_info_ip, global_info_ip_port
global_info_ip = os.environ['GLOBAL_IP']
global_info_ip_port = global_info_ip + ":" + str(FLASK_SVC)

store_class_tasks_dict = {}
store_class_tasks_dict[555] = "storeclass1"
store_class_tasks_dict[779] = "storeclass2"

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
        url = "http://%s:%s/post-id-master"%(global_info_ip,str(FLASK_SVC))
        print(url)
        # request job_id
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        job_id = response.json()
        print(job_id)
    except Exception as e:
        print('Possibly running on the execution profiler')
        job_id = 0

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
        url = "http://%s:%s/post-files-master"%(global_info_ip,str(FLASK_SVC))
        print(url)
        # request job_id
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        next_job_id = response.json()
        print(next_job_id)
    except Exception as e:
        print('Possibly running on the execution profiler')
        job_id = 0

def get_and_send_missing_images():
    # Check with global info server
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None #not using HTTP secure
                                }
    # message for requesting job_id
    payload = {}
    try:
        # url = "http://0.0.0.0:5000/post-id"
        url = "http://%s:%s/post-get-images-master"%(global_info_ip,str(FLASK_SVC))
        print(url)
        # request job_id
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        missing_images_dict = response.json()
        printprint(missing_images_dict)
    except Exception as e:
        print('Possibly running on the execution profiler')
        missing_images_dict = collections.defaultdict(list)
    # Process and send requests out     
    ### Reusing the input files to the master node. NOT creating a local copy of input files.
    logging.debug('Receive missing from decoder task:')
    for image_file, _class in missing_images_dict: 
        logging.debug(image_file)
        file_name_wo_jobid = image_file.split("_jobid_")[0]
        source_path = os.path.join(pathin, file_name_wo_jobid + ".JPEG")
        file_name = 'master_' + image_file
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
    collage_file = create_collage(input_list, collage_spatial, single_spatial, single_spatial_full, w)
    collage_file_split = collage_file.split(".JPEG")[0] 
    shutil.copyfile(collage_file, os.path.join(pathout,"master_"+ collage_file_split + "_jobid_" + str(job_id) + ".JPEG"))
    print('Receive collage file:')
    ### send to collage task
    outlist = [os.path.join(pathout,"master_"+collage_file)]
    print(outlist)
    ### send to resnet tasks
    print('Receive resnet files: ')
    filelist_flask = []
    for i, f in enumerate(filelist):
        idx  = i%num_images
        f_split = f.split(".JPEG")[0]
        f_new = f_split + "_jobid_"+ str(job_id) + ".JPEG" 
        shutil.copyfile(os.path.join(pathin,f), os.path.join(pathout,"master_resnet"+str(idx)+'_'+ f_new))
        filelist_flask.append(f_new)
        outlist.append(os.path.join(pathout,"master_resnet"+str(idx)+'_'+f_new))
        print(outlist)
    next_job_id = put_filenames(filelist_flask)
    get_and_send_missing_images() 
    return outlist

def main():
    filelist = ['n03345487_10.JPEG','n03345487_108.JPEG', 'n03345487_133.JPEG','n03345487_135.JPEG','n03345487_136.JPEG','n04146614_16038.JPEG','n03345487_18.JPEG','n03345487_40.JPEG','n03345487_78.JPEG','n04146614_1.JPEG','n04146614_39.JPEG','n04146614_152.JPEG','n04146614_209.JPEG','n04146614_263.JPEG','n04146614_318.JPEG','n03345487_206.JPEG','n03345487_243.JPEG','n03345487_284.JPEG','n04146614_25.JPEG','n04146614_53.JPEG','n04146614_158.JPEG','n04146614_231.JPEG','n04146614_284.JPEG','n03345487_144.JPEG','n03345487_208.JPEG','n03345487_245.JPEG',
       'n03345487_311.JPEG','n04146614_27.JPEG','n04146614_69.JPEG','n04146614_186.JPEG','n04146614_232.JPEG','n04146614_295.JPEG','n03345487_163.JPEG','n03345487_209.JPEG','n03345487_267.JPEG','n03345487_317.JPEG','n04146614_30.JPEG','n04146614_79.JPEG','n04146614_187.JPEG','n04146614_237.JPEG','n04146614_309.JPEG','n03345487_192.JPEG','n03345487_210.JPEG','n03345487_279.JPEG','n03345487_328.JPEG','n04146614_36.JPEG','n04146614_84.JPEG','n04146614_199.JPEG','n04146614_245.JPEG','n04146614_312.JPEG','n03345487_205.JPEG','n03345487_241.JPEG','n03345487_282.JPEG','n03345487_334.JPEG',
       'n03345487_351.JPEG','n03345487_360.JPEG','n03345487_386.JPEG','n03345487_410.JPEG','n03345487_417.JPEG','n04146614_330.JPEG','n04146614_363.JPEG','n04146614_377.JPEG','n04146614_387.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile

