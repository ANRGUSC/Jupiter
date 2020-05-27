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
        global_info_ip = os.environ['GLOBAL_IP']
        url = "http://%s:%s/post-id-master"%(global_info_ip,str(FLASK_SVC))
        print(url)
        # request job_id
        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        job_id = response.json()
        print(job_id)
    except Exception as e:
        print('Possibly running on the execution profiler')

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
        print(next_job_id)
    except Exception as e:
        print('Possibly running on the execution profiler')

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
        global_info_ip = os.environ['GLOBAL_IP']
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
    next_job_id = put_filenames(job_id, filelist_flask)
    get_and_send_missing_images() 
    return outlist

def main():
    filelist = ['n03345487_10_jobid_0.JPEG','n03345487_108_jobid_0.JPEG', 'n03345487_133_jobid_0.JPEG','n03345487_135_jobid_0.JPEG','n03345487_136_jobid_0.JPEG','n04146614_16038_jobid_0.JPEG','n03345487_18_jobid_0.JPEG','n03345487_40_jobid_0.JPEG','n03345487_78_jobid_0.JPEG','n04146614_1_jobid_0.JPEG','n04146614_39_jobid_0.JPEG','n04146614_152_jobid_0.JPEG','n04146614_209_jobid_0.JPEG','n04146614_263_jobid_0.JPEG','n04146614_318_jobid_0.JPEG','n03345487_206_jobid_0.JPEG','n03345487_243_jobid_0.JPEG','n03345487_284_jobid_0.JPEG','n04146614_25_jobid_0.JPEG','n04146614_53_jobid_0.JPEG','n04146614_158_jobid_0.JPEG','n04146614_231_jobid_0.JPEG','n04146614_284_jobid_0.JPEG','n03345487_144_jobid_0.JPEG','n03345487_208_jobid_0.JPEG','n03345487_245_jobid_0.JPEG',
       'n03345487_311_jobid_0.JPEG','n04146614_27_jobid_0.JPEG','n04146614_69_jobid_0.JPEG','n04146614_186_jobid_0.JPEG','n04146614_232_jobid_0.JPEG','n04146614_295_jobid_0.JPEG','n03345487_163_jobid_0.JPEG','n03345487_209_jobid_0.JPEG','n03345487_267_jobid_0.JPEG','n03345487_317_jobid_0.JPEG','n04146614_30_jobid_0.JPEG','n04146614_79_jobid_0.JPEG','n04146614_187_jobid_0.JPEG','n04146614_237_jobid_0.JPEG','n04146614_309_jobid_0.JPEG','n03345487_192_jobid_0.JPEG','n03345487_210_jobid_0.JPEG','n03345487_279_jobid_0.JPEG','n03345487_328_jobid_0.JPEG','n04146614_36_jobid_0.JPEG','n04146614_84_jobid_0.JPEG','n04146614_199_jobid_0.JPEG','n04146614_245_jobid_0.JPEG','n04146614_312_jobid_0.JPEG','n03345487_205_jobid_0.JPEG','n03345487_241_jobid_0.JPEG','n03345487_282_jobid_0.JPEG','n03345487_334_jobid_0.JPEG',
       'n03345487_351_jobid_0.JPEG','n03345487_360_jobid_0.JPEG','n03345487_386_jobid_0.JPEG','n03345487_410_jobid_0.JPEG','n03345487_417_jobid_0.JPEG','n04146614_330_jobid_0.JPEG','n04146614_363_jobid_0.JPEG','n04146614_377_jobid_0.JPEG','n04146614_387_jobid_0.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile

