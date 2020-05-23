import numpy as np
import time
import os
import cv2
import requests
import json
import configparser
from pathlib import Path
from os import listdir

taskname = Path(__file__).stem
classnum = taskname.split('preagg')[1]

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])

global global_info_ip

def task(filelist, pathin, pathout):     
    filelist = [filelist] if isinstance(filelist, str) else filelist  
    # job_id = filelist[0].partition('_')[2].partition('_')[2].partition('_')[0]
    # job_id = job_id[3:]
    job_id = filelist[0].split('.csv')[0].split('job')[1]
    print(job_id)
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
        job_dict = {'2':['score1a_preagg1_job2.csv','score1b_preagg1_job2.csv']}
        
    #Parameters
    M = 2 # Number of data-batches
    
    #Check if number of received results for the same job is equal to M
    print(filelist[0])
    print(filelist[0].partition('_')[2].partition('_')[2].partition('_')[0])
    print(job_id)
    print(job_dict)
    outlist = []
    if len(job_dict[job_id]) == M:
        print('Receive enough results for job '+job_id)
        for i in range(M):
            print(os.path.join(pathin, (job_dict[job_id])[i]))
            En_Image_Batch = np.loadtxt(os.path.join(pathin, (job_dict[job_id])[i]), delimiter=',')
            destination = os.path.join(pathout,taskname + '_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'.csv')
            np.savetxt(destination, En_Image_Batch, delimiter=',')
            outlist.append(destination)
    else:
        print('Not receive enough results for job '+job_id)
    return outlist

def main():
    # file1 = 'score%sa_preagg%s_job1_20200424.csv'%(classnum,classnum)
    # filelist= [file1]  
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    c = 'score%s'%(classnum)
    filelist = [f for f in listdir(outpath) if f.startswith(c)]
    outfile = task(filelist, outpath, outpath)
    return outfile

