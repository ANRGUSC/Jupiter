import numpy as np
import time
import os
import cv2
import requests
import json
import configparser
from pathlib import Path
from os import listdir
import logging
import time

from datetime import datetime
global circe_home_ip, circe_home_ip_port, taskname
import urllib
import numpy as np

logging.basicConfig(level = logging.DEBUG)
taskname = Path(__file__).stem
classnum = taskname.split('preagg')[1]

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
FLAG_PART2 = int(config['OTHER']['FLAG_PART2'])

global global_info_ip

classlist = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard', 'lion',  'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
classids = np.arange(0,len(classlist),1)
classmap = dict(zip(classlist, classids))

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

def send_runtime_stats(action, file_name, fromtask):
    ts = time.time()
    new_file = os.path.split(file_name)[-1]
    original_name = new_file.split('.')[0]
    logging.debug(original_name)
    tmp_name = original_name.split('_')[-1]
    temp_name= tmp_name+'.JPEG'
    runtime_info = action +' '+ temp_name+ ' '+str(ts) 
    send_runtime_profile(runtime_info)


def task(filelist, pathin, pathout):     
    filelist = [filelist] if isinstance(filelist, str) else filelist  

    for f in filelist:
        send_runtime_stats('rt_enter_task', f)

    job_id = filelist[0].split('.csv')[0].split('_')[-2].split('job')[1]
    print(job_id)
    filesuffixs = filelist[0].split('.csv')[0].split('_')[-1]
    print(filesuffixs)
    
    # job_id = int(job_id)
    
    
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None 
                                }
    # the message of requesting dictionary
    # payload = {
    #     'job_id': job_id,
    #     'filename': filelist[0]
    # }
    payload = {
        'class_image': int(classnum),
        'job_id': job_id,
        'filename': filelist[0]
    }
    
    # address of flask server for class1 is 0.0.0.0:5000 and "post-dict" is for requesting dictionary 
    try:
        # url = "http://0.0.0.0:5000/post-dict"
        global_info_ip = os.environ['GLOBAL_IP']
        url = "http://%s:%s/post-dict"%(global_info_ip,str(FLASK_SVC))
        print(url)
        # request of dictionary of received results
        response =  requests.post(url, headers = hdr,data = json.dumps(payload))
        job_dict = response.json()
        print(job_dict)
    except Exception as e:
        print('Possibly running on the execution profiler')
        if FLAG_PART2 == 1:
            sample1 = [f for f in listdir(pathout) if f.startswith('score2a_preagg2_job2')]
            sample2 = [f for f in listdir(pathout) if f.startswith('score2b_preagg2_job2')]
            job_dict = {'2':[sample1[0],sample2[0]]}
        else:
            sample1 = [f for f in listdir(pathout) if f.startswith('score2a_preagg2_job2')]
            sample2 = [f for f in listdir(pathout) if f.startswith('score2b_preagg2_job2')]
            sample3 = [f for f in listdir(pathout) if f.startswith('score2c_preagg2_job2')]
            job_dict = {'2':[sample1[0],sample2[0],sample3[0]]}
        
    #Parameters
    M = 2 # Number of data-batches
    N = 3 # Number of workers
    
    if FLAG_PART2: #Coding Version
        #Check if number of received results for the same job is equal to M
        outlist = []
        if len(job_dict[job_id]) == M:
            print('Receive enough results for job '+job_id)
            for i in range(M):
                print(job_id)
                print(job_dict[job_id])
                print(os.path.join(pathin, (job_dict[job_id])[i]))
                En_Image_Batch = np.loadtxt(os.path.join(pathin, (job_dict[job_id])[i]), delimiter=',')
                # destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'.csv')
                destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'_'+filesuffixs+'.log')
                np.savetxt(destination, En_Image_Batch, delimiter=',')
                outlist.append(destination)
                send_runtime_stats('rt_finish_task', destination)
        else:
            print('Not receive enough results for job '+job_id)

        
        return outlist
    
    else:
        #Check if number of received results for the same job is equal to N
        outlist = []
        if len(job_dict[job_id]) == N:
            print('Receive enough results for job '+job_id)
            for i in range(N):
                En_Image_Batch = np.loadtxt(os.path.join(pathin, (job_dict[job_id])[i]), delimiter=',')
                # destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'.csv')
                destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'_'+filesuffixs+'.log')
                np.savetxt(destination, En_Image_Batch, delimiter=',')
                outlist.append(destination)
                send_runtime_stats('rt_finish_task', destination)
        else:
            print('Not receive enough results for job '+job_id)

            
        return outlist

    
    
def main():
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    c = 'score%s'%(classnum)
    filelist = [f for f in listdir(outpath) if f.startswith(c)]
    logging.debug(filelist)
    outfile = task(filelist, outpath, outpath)
    return outfile
