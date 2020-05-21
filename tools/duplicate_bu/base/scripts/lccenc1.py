import numpy as np
import time
import os
import cv2
import requests
import json
import configparser
from pathlib import Path

taskname = Path(__file__).stem
classnum = taskname.split('lccenc')[1]

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])

global global_info_ip


def gen_Lagrange_coeffs(alpha_s,beta_s):
    U = np.zeros((len(alpha_s), len(beta_s)))
    for i in range(len(alpha_s)):
        for j in range(len(beta_s)):
            cur_beta = beta_s[j];
            den = np.prod([cur_beta - o   for o in beta_s if cur_beta != o])
            num = np.prod([alpha_s[i] - o for o in beta_s if cur_beta != o])
            U[i][j] = num/den 
    return U


def LCC_encoding(X,N,M):
    w,l = X[0].shape
    n_beta = M
    beta_s, alpha_s = range(1,1+n_beta), range(1+n_beta,N+1+n_beta)

    U = gen_Lagrange_coeffs(alpha_s,beta_s)
    X_LCC = []
    for i in range(N):
        X_zero = np.zeros(X[0].shape)
        for j in range(M):
            X_zero = X_zero + U[i][j]*X[j]
        X_LCC.append(X_zero)
    return X_LCC



def task(filelist, pathin, pathout):    
    filelist = [filelist] if isinstance(filelist, str) else filelist  
    snapshot_time = filelist[0].partition('_')[2].partition('.')[0]  #store the data&time info 
    
    hdr = {
            'Content-Type': 'application/json',
            'Authorization': None #not using HTTP secure
                                }
    # message for requesting job_id
    # payload = {'event': 'request id'}
    payload = {'class_image': int(classnum)}
    # address of flask server for class1 is 0.0.0.0:5000 and "post-id" is for requesting id
    try:
        # url = "http://0.0.0.0:5000/post-id"
        global_info_ip = os.environ['GLOBAL_IP']
        url = "http://%s:%s/post-id"%(global_info_ip,str(FLASK_SVC))
        print(url)
        # request job_id

        response = requests.post(url, headers = hdr, data = json.dumps(payload))
        job_id = response.json()
        printprint(job_id)
    except Exception as e:
        print('Possibly running on the execution profiler')
        job_id = 2

    # Parameters
    # L = 10 # Number of images in a data-batch
    L = 2 # Number of images in a data-batch
    M = 2 # Number of data-batches
    N = 3 # Number of workers (encoded data-batches)
    
    # Dimension of resized image
    width = 400
    height = 400
    dim = (width, height)
    
    
    #Read M batches

    Image_Batch = []
    count_file = 0
    for j in range(M):
        count = 0
        while count < L:
            img = cv2.imread(os.path.join(pathin, filelist[count_file])) 
            if img is not None:
            # resize image
                img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
                img = np.float64(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)) 
                img -= img.mean()
                img /= img.std()
                img_w ,img_l = img.shape
                img = img.reshape(1,img_w*img_l)
                if count == 0:
                   Images = img
                else:
                   Images = np.concatenate((Images,img), axis=0)  
                count+=1
            count_file+=1
        Image_Batch.append(Images)
    
    # Encode M data batches to N encoded data
    En_Image_Batch = LCC_encoding(Image_Batch,N,M)
    
    out_list = []
    
    # Save each encoded data-batch i to a csv 
    for i in range(N):
        destination = os.path.join(pathout,taskname,'_score'+classnum+chr(i+97)+'_'+'job'+str(job_id)+'_'+snapshot_time+'.csv')
        np.savetxt(destination, En_Image_Batch[i], delimiter=',')
        out_list.append(destination)
    return out_list

def main():
    file1 = 'storeclass%s_resnet0_storeclass1_master_resnet0_n03345487_10.JPEG'%(classnum)
    file2 = 'storeclass%s_resnet1_storeclass1_master_resnet1_n03345487_108.JPEG'%(classnum)
    file3 = 'storeclass%s_resnet2_storeclass1_master_resnet2_n03345487_133.JPEG'%(classnum)
    file4 = 'storeclass%s_resnet3_storeclass1_master_resnet3_n03345487_135.JPEG'%(classnum)
    file5 = 'storeclass%s_resnet4_storeclass1_master_resnet4_n03345487_136.JPEG'%(classnum)
    file6 = 'storeclass%s_resnet5_storeclass1_master_resnet5_n03345487_144.JPEG'%(classnum)
    file7 = 'storeclass%s_resnet5_storeclass1_master_resnet5_n03345487_163.JPEG'%(classnum)
    file8 = 'storeclass%s_resnet5_storeclass1_master_resnet5_n03345487_192.JPEG'%(classnum)
    file9 = 'storeclass%s_resnet5_storeclass1_master_resnet5_n03345487_205.JPEG'%(classnum)
    file10 = 'storeclass%s_resnet6_storeclass1_master_resnet6_n03345487_18.JPEG'%(classnum)
    file11 = 'storeclass%s_resnet6_storeclass1_master_resnet6_n03345487_206.JPEG'%(classnum)
    file12 = 'storeclass%s_resnet6_storeclass1_master_resnet6_n03345487_208.JPEG'%(classnum)
    file13 = 'storeclass%s_resnet6_storeclass1_master_resnet6_n03345487_209.JPEG'%(classnum)
    file14 = 'storeclass%s_resnet6_storeclass1_master_resnet6_n03345487_210.JPEG'%(classnum)
    file15 = 'storeclass%s_resnet6_storeclass1_master_resnet6_n03345487_241.JPEG'%(classnum)
    file16 = 'storeclass%s_resnet7_storeclass1_master_resnet7_n03345487_40.JPEG'%(classnum)
    file17 = 'storeclass%s_resnet7_storeclass1_master_resnet7_n03345487_243.JPEG'%(classnum)
    file18 = 'storeclass%s_resnet7_storeclass1_master_resnet7_n03345487_245.JPEG'%(classnum)
    file19 = 'storeclass%s_resnet7_storeclass1_master_resnet7_n03345487_267.JPEG'%(classnum)
    file20 = 'storeclass%s_resnet7_storeclass1_master_resnet7_n03345487_279.JPEG'%(classnum)
    file21 = 'storeclass%s_resnet7_storeclass1_master_resnet7_n03345487_282.JPEG'%(classnum)
    file22 = 'storeclass%s_resnet8_storeclass1_master_resnet8_n03345487_78.JPEG'%(classnum)
    file23 = 'storeclass%s_resnet8_storeclass1_master_resnet8_n03345487_284.JPEG'%(classnum)
    file24 = 'storeclass%s_resnet8_storeclass1_master_resnet8_n03345487_311.JPEG'%(classnum)
    file25 = 'storeclass%s_resnet8_storeclass1_master_resnet8_n03345487_317.JPEG'%(classnum)
    file26 = 'storeclass%s_resnet8_storeclass1_master_resnet8_n03345487_328.JPEG'%(classnum)
    file27 = 'storeclass%s_resnet8_storeclass1_master_resnet8_n03345487_334.JPEG'%(classnum)
    file28 = 'storeclass%s_resnet0_storeclass1_master_resnet0_n03345487_351.JPEG'%(classnum)
    file29 ='storeclass%s_resnet1_storeclass1_master_resnet1_n03345487_360.JPEG'%(classnum)
    file30 = 'storeclass%s_resnet2_storeclass1_master_resnet2_n03345487_386.JPEG'%(classnum)
    file31 = 'storeclass%s_resnet3_storeclass1_master_resnet3_n03345487_410.JPEG'%(classnum)
    file32 = 'storeclass%s_resnet4_storeclass1_master_resnet4_n03345487_417.JPEG'%(classnum)
    filelist = [file1,file2,file3,file4,file5,file6,file7,file8,file9,file10,file11,file2,file13,file14,file15,file16,file17,file18,file19,file20,file21,
    file22,file23,file24,file25,file26,file27,file28,file29,file30,file31,file32] 
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
