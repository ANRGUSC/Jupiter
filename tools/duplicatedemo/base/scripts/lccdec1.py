import numpy as np
import time
import os
import cv2
import configparser
from pathlib import Path
from os import listdir
import logging
from datetime import datetime
import urllib
import time
import numpy as np

global circe_home_ip, circe_home_ip_port, taskname

logging.basicConfig(level = logging.DEBUG)

taskname = Path(__file__).stem
classnum = taskname.split('lccdec')[1]

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
FLAG_PART2 = int(config['OTHER']['FLAG_PART2'])

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

def send_runtime_stats(action, file_names):
    ts = time.time()
    for i in range(0,len(file_names)):
        file_name = file_names[i]
        new_file = os.path.split(file_name)[-1]
        original_name = new_file.split('.')[0]
        logging.debug(original_name)
        tmp_name = original_name.split('_')[-1]
        temp_name= tmp_name+'.JPEG'
        runtime_info = action +' '+ temp_name+ ' '+str(ts)
        send_runtime_profile(runtime_info)
        
def gen_Lagrange_coeffs(alpha_s,beta_s):
    U = np.zeros((len(alpha_s), len(beta_s)))
    for i in range(len(alpha_s)):
        for j in range(len(beta_s)):
            cur_beta = beta_s[j];
            den = np.prod([cur_beta - o   for o in beta_s if cur_beta != o])
            num = np.prod([alpha_s[i] - o for o in beta_s if cur_beta != o])
            U[i][j] = num/den 
    return U

def LCC_decoding(f_eval,N,M,worker_idx):
    n_beta = M
    beta_s, alpha_s = range(1,1+n_beta), range(1+n_beta,N+1+n_beta)
    alpha_s_eval = [alpha_s[i] for i in worker_idx]
    U_dec = gen_Lagrange_coeffs(beta_s,alpha_s_eval)
    f_recon = []
    for i in range(M):        
        for j in range(M):
            if j ==0:
                x_zero = U_dec[i][j]*np.asarray([f_eval[j]])
            else:
                x_zero = x_zero + U_dec[i][j]*np.asarray([f_eval[j]])
        f_recon.append(x_zero)
    return f_recon



FLAG_PART2 = int(config['OTHER']['FLAG_PART2'])

def task(filelist, pathin, pathout): 
    filelist = [filelist] if isinstance(filelist, str) else filelist  

    send_runtime_stats('rt_enter_task', filelist)
    #snapshot_time = filelist[0].partition('_')[2].partition('_')[2].partition('_')[2].partition('_')[2].partition('.')[0]  #store the data&time info 
    
    # Load id of incoming job (id_job=1,2,3,...)
    # job_id = filelist[0].partition('_')[2].partition('_')[2].partition('_')[2].partition('.')[0]
    # job_id = job_id[3:]
    job_id = filelist[0].split('_')[-2].split('job')[1]
    print(job_id)
    filesuffixs = filelist[0].split('_')[-1]
    print(filesuffixs)
   
    #Parameters 
    N = 3 # Number of workers (encoded data-batches)
    M = 2 # Number of data-batches
    K = 10 # Number of referenced Images
    
    if FLAG_PART2:
        # Results recieved from M workers
        worker_idx = [ord((filelist[i].partition('_')[2].partition('_')[2].partition('_')[0])[6])-97 for i in range(M)]
        worker_eval = [np.loadtxt(os.path.join(pathin, filelist[i]), delimiter=',') for i in range(M)]

        # Decoding Process 
        results = [] 
        for i in range(K):
            f_eval = []
            for j in range(M):
                a = worker_eval[j]
                f_eval.append(a[i,:])  
            f_dec = LCC_decoding(f_eval,N,M,worker_idx) 
            if i ==0:
                for j in range(M):
                    results.append(f_dec[j])
            else:
                for j in range(M):
                    results[j] = np.concatenate((results[j],f_dec[j]), axis = 0)


        #Save desired scores of M data-batches
        outlist = []
        for j in range(M):
            if j== 0:
                result = results[j]
            else:
                result = np.concatenate((result, results[j]), axis = 0)
        destination = os.path.join(pathout,'job'+job_id+'_'+taskname+'_'+filesuffixs)
        np.savetxt(destination, result, delimiter=',')
        outlist.append(destination)

        send_runtime_stats('rt_finish_task', outlist)
        return outlist
    else:
        # Results recieved from N workers
        worker_idx = [ord((filelist[i].partition('_')[2].partition('_')[2].partition('_')[0])[6])-97 for i in range(N)]
        worker_eval = [np.loadtxt(os.path.join(pathin, filelist[i]), delimiter=',') for i in range(N)]

        # Decoding Process 
        results = [] 
        for i in range(K):
            f_eval = []
            for j in range(N):
                a = worker_eval[j]
                f_eval.append(a[i,:])  
            f_dec = LCC_decoding(f_eval,N,N,worker_idx) 
            if i ==0:
                for j in range(N):
                    results.append(f_dec[j])
            else:
                for j in range(N):
                    results[j] = np.concatenate((results[j],f_dec[j]), axis = 0)


        #Save desired scores of M data-batches
        outlist = []
        for j in range(M):
            if j== 0:
                result = results[j]
            else:
                result = np.concatenate((result, results[j]), axis = 0)
        destination = os.path.join(pathout,taskname+'_'+'job'+job_id+'_'+filesuffixs)
        np.savetxt(destination, result, delimiter=',')
        outlist.append(destination)

        send_runtime_stats('rt_finish_task', outlist)
        
        return outlist

def main():
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    c = 'preagg%s'%(classnum)
    filelist = [f for f in listdir(outpath) if f.startswith(c)]
    logging.debug(filelist)
    outfile = task(filelist, outpath, outpath)
    return outfile