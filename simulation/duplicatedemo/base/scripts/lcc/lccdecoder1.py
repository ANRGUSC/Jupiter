import numpy as np
import time
import os
import cv2

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


def task(filelist, pathin, pathout): 
    snapshot_time = filelist[0].partition('_')[2].partition('_')[2].partition('_')[2].partition('_')[2].partition('.')[0]  #store the data&time info 
    
    # Load id of incoming job (id_job=1,2,3,...)
    job_id = filelist[0].partition('_')[2].partition('_')[2].partition('_')[2].partition('_')[0]
    job_id = job_id[3:]
   
    #Parameters 
    N = 3 # Number of workers (encoded data-batches)
    M = 2 # Number of data-batches
    K = 10 # Number of referenced Images

    # Results recieved from M workers
    worker_idx = [ord((b.partition('_')[2].partition('_')[2].partition('_')[0])[6])-97 for i in range(M)]
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
    for j in range(M):
        np.savetxt(os.path.join(pathout,'job'+job_id+'outlccdecoder'+str(j)+'_'+snapshot_time+'.csv'), results[j], delimiter=',')

if __name__ == '__main__': ##THIS IS FOR TESTING - DO THIS
    filelist= ['preaggregator1_lccdecoder1_score1a_job1_20200424.csv','preaggregator1_lccdecoder1_score1c_job1_20200424.csv'] 
    task(filelist,'./Agg_Results1', './Results1') 
