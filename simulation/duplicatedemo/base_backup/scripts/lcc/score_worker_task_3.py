import numpy as np
import time
import os
import cv2

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
    snapshot_time = filelist[0].partition('_')[2].partition('.')[0]  #store the data&time info 
    
    # Load id of incoming job (id_job=1,2,3,...)
    job_id = filelist[0].partition('encdata')[0]
    job_id = job_id[3:]
    

    #Worker ID: 1,2,...,N
    worker_id = 3
    
    #Parameters
    K = 10 # Number of referenced Images
    
    # Dimension of resized image
    width = 400
    height = 400
    dim = (width, height)   
    
    # Read Reference Images
    filelist_ref = ['fireengine'+str(i+1)+'_20200424.jpg' for i in range(20,30)]  # to be defined in advance
    path_ref = './fireengine' # folder of referenced images
    
    for i in range(K):
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
    En_Image_Batch = np.loadtxt(os.path.join(pathin, filelist[worker_id]), delimiter=',')
    
    
    # Compute Scores of ref images and En_Images
    sc = score(En_Image_Batch, Ref_Images)
    
    # Save the encoded score to a csv file 
    np.savetxt(os.path.join(pathout,'job'+job_id+'encsc'+str(worker_id)+'_'+snapshot_time+'.csv'), sc, delimiter=',')
    
if __name__ == '__main__': ##THIS IS FOR TESTING - DO THIS
    filelist= ['job1encdata'+str(i+1)+'_20200424.csv' for i in range(3)] 
    task(filelist,'./Enc_Data', './Enc_Results') 
