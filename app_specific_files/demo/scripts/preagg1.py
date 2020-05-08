import numpy as np
import time
import os
import cv2
import requests
import json


def task(filelist, pathin, pathout):     
    snapshot_time = filelist[0].partition('_')[2].partition('_')[2].partition('_')[2].partition('.')[0]  #store the data&time info 
    job_id = filelist[0].partition('_')[2].partition('_')[2].partition('_')[0]
    job_id = job_id[3:]
    
    
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None 
                                }
    # the message of requesting dictionary
    payload = {
        'job_id': job_id,
        'filename': filelist[0]
    }
    
    # address of flask server for class1 is 0.0.0.0:5000 and "post-dict" is for requesting dictionary 
    try:
        url = "http://0.0.0.0:5000/post-dict"
        
        # request of dictionary of received results
        job_dict = requests.post(url, headers = hdr,data = json.dumps(payload))
    except Exception as e:
        print('Possibly running on the execution profiler')
        # job_dict = {'1':['score1a_preagg1_job1_20200424.csv', 'score1b_preagg1_job1_20200424.csv']}
        job_dict = {'1':['score1a_preagg1_job2_resnet0_storeclass1_master_resnet0_n03345487_10.csv','score1b_preagg1_job2_resnet0_storeclass1_master_resnet0_n03345487_10.csv']}
        
    #Parameters
    M = 2 # Number of data-batches
    
    #Check if number of received results for the same job is equal to M
    outlist = []
    if len(job_dict[job_id]) == M:
        print('Receive enough results for job '+job_id)
        for i in range(M):
            En_Image_Batch = np.loadtxt(os.path.join(pathin, (job_dict[job_id])[i]), delimiter=',')
            destination = os.path.join(pathout,'preagg1_lccdec1_'+filelist[0].partition('_')[0]+'_job'+job_id+'_'+snapshot_time+'.csv')
            np.savetxt(destination, En_Image_Batch, delimiter=',')
            outlist.append(destination)
    else:
        print('Not receive enough results for job '+job_id)
    return outlist

def main():
    filelist= ['score1a_preagg1_job1_20200424.csv']  
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile

