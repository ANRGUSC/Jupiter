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
    url = "http://0.0.0.0:5000/post-dict"
    
    # request of dictionary of received results
    job_dict = requests.post(url, headers = hdr,ata = json.dumps(payload))
        
    #Parameters
    M = 2 # Number of data-batches
    
    #Check if number of received results for the same job is equal to M
    if len(job_dict[job_id]) == M:
        print('Receive enough results for job '+job_id)
        for i in range(M):
            En_Image_Batch = np.loadtxt(os.path.join(pathin, (job_dict[job_id])[i]), delimiter=',')
            np.savetxt(os.path.join(pathout,'preaggregator1_lccdecoder1_'+filelist[0].partition('_')[0]+'_job'+job_id+'_'+snapshot_time+'.csv'), En_Image_Batch, delimiter=',')
    else:
        print('Not receive enough results for job '+job_id)
            
if __name__ == '__main__': ##THIS IS FOR TESTING - DO THIS
    filelist= ['score1a_preaggregator1_job1_20200424.csv'] 
    task(filelist,'./Enc_Results', './Agg_Results')  
