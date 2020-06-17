import numpy as np
import time
import os
import cv2
from pathlib import Path
from os import listdir
import configparser
import random
global logging
import logging 
import urllib
logging.basicConfig(level = logging.DEBUG)

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)
global SLEEP_TIME, STRAGGLER_THRESHOLD
SLEEP_TIME   = int(config['OTHER']['SLEEP_TIME'])
STRAGGLER_THRESHOLD   = float(config['OTHER']['STRAGGLER_THRESHOLD'])


from datetime import datetime
global circe_home_ip, circe_home_ip_port, taskname

global FLASK_DOCKER, FLASK_SVC, num_retries, ssh_port, username, password, CODING_PART1
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
ssh_port    = int(config['PORT']['SSH_SVC'])
username    = config['AUTH']['USERNAME']
password    = config['AUTH']['PASSWORD']

taskname = Path(__file__).stem
classnum = taskname.split('score')[1][0]
classlist = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard', 'lion',  'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
classname = classlist[int(classnum)-1]

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

# Similarity score (zero-normalized cross correlation)
def score (En_Image_Batch, Ref_Images):
    K, F = Ref_Images.shape
    L, F = En_Image_Batch.shape
    ref_scores = np.zeros((K,L)) # K * length(vector)
    for i in range(K):
        for j in range(L):
            ref_scores[i,j] = np.mean(np.correlate(En_Image_Batch[j], Ref_Images[i]))
    return ref_scores


def task(filelist, pathin, pathout):   
    filelist = [filelist] if isinstance(filelist, str) else filelist  
    send_runtime_stats('rt_enter_task', filelist)
    #snapshot_time = filelist[0].partition('_')[2].partition('_')[2].partition('_')[2].partition('.')[0]  #store the data&time info 
    
    # Load id of incoming job (id_job=1,2,3,...)
    #job_id = filelist[0].partition('outlccencoder')[0]
    # job_id = filelist[0].partition('_')[2].partition('_')[2].partition('.')[0]
    # job_id = job_id[3:]
    job_id = filelist[0].split('.csv')[0].split('_')[-2].split('job')[1]
    
    filesuffixs = filelist[0].split('.csv')[0].split('_')[-1]
    

    #Worker ID: a,b,c,...
    worker_id = 'b'
    
    #Parameters
    K = 10 # Number of referenced Images
    
    # Dimension of resized image
    width = 400
    height = 400
    dim = (width, height)   
    
    # Read Reference Images
    # filelist_ref = ['fireengine'+str(i+1)+'_20200424.jpg' for i in range(20,30)]  # to be defined in advance
    # path_ref = os.path.join(os.path.dirname(__file__),'fireengine') # folder of referenced images
    # Read Reference Images
    filelist_ref = [classname+str(i+1)+'.JPEG' for i in range(20,30)]  # to be defined in advance
    path_ref = os.path.join(os.path.dirname(__file__),'reference',classname) # folder of referenced images

    for i in range(K):
        print(os.path.join(path_ref, filelist_ref[i]))
        img = cv2.imread(os.path.join(path_ref, filelist_ref[i]))
        img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
        img = np.float64(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)) 
        img -= img.mean()
        img /= img.std()
        img_w ,img_l = img.shape
        img = img.reshape(1,img_w*img_l)
        if i == 0:
            Ref_Images = img
        else:
            Ref_Images = np.concatenate((Ref_Images,img), axis=0)   

    ### To simulate slow downs
    # purposely add delay time to slow down the sending
    if (random.random() > STRAGGLER_THRESHOLD) and (classnum=='a'):
        print(classnum)
        print("Sleeping")
        time.sleep(SLEEP_TIME) #>=2  
    
    
    # Read Encoded data-batch   
    En_Image_Batch = np.loadtxt(os.path.join(pathin, filelist[0]), delimiter=',')
    
    
    # Compute Scores of ref images and En_Images
    sc = score(En_Image_Batch, Ref_Images)
    
    outlist = []
    # destination = os.path.join(pathout,'score1' + worker_id + '_'+'preagg1'+ '_' +'job' + job_id +'.csv')
    destination = os.path.join(pathout,'score'+classnum + worker_id + '_'+'preagg'+classnum+ '_' +'job' + job_id +'_'+filesuffixs+'.csv')
    np.savetxt(destination, sc, delimiter=',')
    outlist.append(destination)
    send_runtime_stats('rt_finish_task', outlist)
    return outlist

def main():
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    c = 'lccenc%s'%(classnum)
    filelist = [f for f in listdir(outpath) if f.startswith(c)]
    outfile = task(filelist, outpath, outpath)
    return outfile
