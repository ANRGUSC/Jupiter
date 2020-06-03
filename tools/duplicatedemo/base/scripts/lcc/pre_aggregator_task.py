import numpy as np
import time
import os
import cv2

def task(filelist, pathin, pathout):     
    job_id = filelist[0].partition('encsc')[0]
    job_id = job_id[3:]
    
    # Load Dictionary of recieved results
    dict_path = '/Job_Dictionary/job_dictionary.txt' # to de defined in advacne
    with open(dict_path,'r') as inf:
        job_dict = eval(inf.read())
    
    #Parameters
    M = 2 # Number of data-batches
    
    #Update Dictionanry
    job_dict[job_id].append(filelist[0])
    with open('./Job_Dictionary/job_dictionary.txt', 'w') as outfile:
        json.dump(job_dict, outfile)
    
    #Check if number of received results for the same job is equal to M
    if len(job_dict[job_id]) == M:
        for i in range(M):
            En_Image_Batch = np.loadtxt(os.path.join(pathin, (job_dict[job_id])[i]), delimiter=',')
            np.savetxt(os.path.join(pathout,(job_dict[job_id])[i]), En_Image_Batch, delimiter=',')

            
if __name__ == '__main__': ##THIS IS FOR TESTING - DO THIS
    filelist= ['job1encsc1_20200424.csv'] 
    task(filelist,'./Enc_Results', './Agg_Results')  
