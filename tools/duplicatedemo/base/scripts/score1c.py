import numpy as np
import time
import os
import cv2
from pathlib import Path
from os import listdir

taskname = Path(__file__).stem
classnum = taskname.split('score')[1][0]
classlist = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'kitfox', 'persiancat', 'leopard', 'lion', 'tiger', 'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
classname = classlist[int(classnum)-1]

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
    #snapshot_time = filelist[0].partition('_')[2].partition('_')[2].partition('_')[2].partition('.')[0]  #store the data&time info 
    
    # Load id of incoming job (id_job=1,2,3,...)
    #job_id = filelist[0].partition('outlccencoder')[0]
    # job_id = filelist[0].partition('_')[2].partition('_')[2].partition('.')[0]
    # job_id = job_id[3:]
    job_id = filelist[0].split('.csv')[0].split('job')[1]
    print(job_id)
    

    #Worker ID: a,b,c,...
    worker_id = 'c'
    
    #Parameters
    K = 10 # Number of referenced Images
    
    # Dimension of resized image
    width = 400
    height = 400
    dim = (width, height)   
    
    # # Read Reference Images
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
    
    
    # Read Encoded data-batch   
    En_Image_Batch = np.loadtxt(os.path.join(pathin, filelist[0]), delimiter=',')
    
    
    # Compute Scores of ref images and En_Images
    sc = score(En_Image_Batch, Ref_Images)
    
    # Save the encoded score to a csv file 
    outlist = []
    #destination = os.path.join(pathout,'score1' + worker_id + '_'+'preagg1'+ '_' +'job' + job_id +'.csv')
    destination = os.path.join(pathout,'score'+classnum + worker_id + '_'+'preagg'+classnum+ '_' +'job' + job_id +'.csv')
    np.savetxt(destination, sc, delimiter=',')
    outlist.append(destination)
    return outlist

def main():
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    c = 'lccenc%s'%(classnum)
    filelist = [f for f in listdir(outpath) if f.startswith(c)]
    outfile = task(filelist, outpath, outpath)
    return outfile
        
        
