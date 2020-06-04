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



def task(filelist, pathin, pathout):     
    filelist = [filelist] if isinstance(filelist, str) else filelist  
    #snapshot_time = filelist[0].partition('_')[2].partition('_')[2].partition('_')[2].partition('.')[0]  #store the data&time info 
    # job_id = filelist[0].partition('_')[2].partition('_')[2].partition('.')[0]
    # job_id = job_id[3:]
    job_id = filelist[0].split('_')[2].split('job')[1]
    print(job_id)
    filesuffixs = filelist[0].split('_')[3:]
    print(filesuffixs)
    filesuffix = '_'.join(filesuffixs)
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
        sample1 = [f for f in listdir(pathout) if f.startswith('score2a_preagg2_job2')]
        sample2 = [f for f in listdir(pathout) if f.startswith('score2b_preagg2_job2')]
        job_dict = {'2':[sample1[0],sample2[0]]}
        
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
                destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'_'+filesuffix)
                np.savetxt(destination, En_Image_Batch, delimiter=',')
                outlist.append(destination)
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
                destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'_'+filesuffix)
                np.savetxt(destination, En_Image_Batch, delimiter=',')
                outlist.append(destination)
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
