import os
import shutil
import sys
import queue
import threading
import logging
import glob
import time
import json

from os import listdir
import numpy as np
import configparser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
    sys.path.append("/jupiter/build/app_specific_files/")
    from jupiter_utils import app_config_parser
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../mulhome_scripts/")
    from jupiter_utils import app_config_parser

import ccdag

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)

#task config information
config = configparser.ConfigParser()
config.read(ccdag.JUPITER_CONFIG_INI_PATH)


classids = np.arange(0,len(ccdag.classlist),1)
classmap = dict(zip(ccdag.classlist, classids))

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
# Run by dispatcher (e.g. CIRCE). Use task_name to differentiate the tasks by
# name to reuse one base task file.
def task(q, pathin, pathout, task_name):
    children = app_config.child_tasks(task_name)
    class_num = task_name.split('lccdec')[1]
    #Parameters
    N = 3 # Number of workers (encoded data-batches)
    M = 2 # Number of data-batches
    K = 10 # Number of referenced Images

    while True:
        if ccdag.CODING_PART2:
            num_inputs = 2
            input_list = []
            src_list = []
            base_list = []
            id_list = []
            worker_list =[]
            for i in range(0,num_inputs): #number of inputs is 9
                input_file = q.get()
                input_list.append(input_file)
                src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
                log.info(f"{task_name}: file rcvd from {src_task} : {input_file}")
                src = os.path.join(pathin, input_file)
                src_list.append(src)
                base_list.append(base_fname)
                id_list.append(base_fname.split('jobth')[1])
                worker = base_fname.split('score')[1]
                worker_list.append(ord(worker[1])-97)


            start = time.time()

            #LCCDEC CODE
            job_id = base_fname.split('jobth')[0]
            file_id = worker[2:]

            # Results recieved from M workers
            worker_eval = [np.loadtxt(src_list[i], delimiter=',') for i in range(M)]
            # Decoding Process
            results = []
            for i in range(K):
                f_eval = []
                for j in range(M):
                    a = worker_eval[j]
                    f_eval.append(a[i,:])
                f_dec = LCC_decoding(f_eval,N,M,worker_list)
                if i ==0:
                    for j in range(M):
                        results.append(f_dec[j])
                else:
                    for j in range(M):
                        results[j] = np.concatenate((results[j],f_dec[j]), axis = 0)


            #Save desired scores of M data-batches
            for j in range(M):
                if j== 0:
                    result = results[j]
                else:
                    result = np.concatenate((result, results[j]), axis = 0)

            job = str(job_id)+'jobth'
            dst_task = children[0] # only 1 children
            dst = os.path.join(pathout, f"{task_name}_{dst_task}_{job}{file_id}")
            np.savetxt(dst, result, delimiter=',')

            # read the generate output
            # based on that determine sleep and number of bytes in output file
            end = time.time()
            runtime_stat = {
                "task_name" : task_name,
                "start" : start,
                "end" : end
            }
            log.warning(json.dumps(runtime_stat))
            for i in range(num_inputs):
                q.task_done()

        else:
            num_inputs = 3
            input_list = []
            src_list = []
            base_list = []
            id_list = []
            worker_list =[]
            for i in range(0,num_inputs): #number of inputs is 9
                input_file = q.get()
                input_list.append(input_file)
                src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
                log.info(f"{task_name}: file rcvd from {src_task} : {input_file}")
                src = os.path.join(pathin, input_file)
                src_list.append(src)
                base_list.append(base_fname)
                id_list.append(base_fname.split('jobth')[1])
                worker = base_fname.split('score')[1]
                worker_list.append(ord(worker[1])-97)


            start = time.time()

            #LCCDEC CODE
            job_id = base_fname.split('jobth')[0]
            file_id = worker[2:]

            # Results recieved from N workers
            #worker_idx = [ord((input_list[i].partition('_')[2].partition('_')[2].partition('_')[0])[6])-97 for i in range(N)]
            worker_eval = [np.loadtxt(os.path.join(pathin, input_list[i]), delimiter=',') for i in range(N)]

            # Decoding Process
            results = []
            for i in range(K):
                f_eval = []
                for j in range(N):
                    a = worker_eval[j]
                    f_eval.append(a[i,:])
                f_dec = LCC_decoding(f_eval,N,N,worker_list)
                if i ==0:
                    for j in range(N):
                        results.append(f_dec[j])
                else:
                    for j in range(N):
                        results[j] = np.concatenate((results[j],f_dec[j]), axis = 0)


            #Save desired scores of M data-batches
            for j in range(M):
                if j== 0:
                    result = results[j]
                else:
                    result = np.concatenate((result, results[j]), axis = 0)
            job = str(job_id)+'jobth'
            dst_task = children[0] # only 1 children
            dst = os.path.join(pathout, f"{task_name}_{dst_task}_{job}{file_id}")
            # destination = os.path.join(pathout,taskname+'_job'+job_id+'_'+filesuffixs)
            np.savetxt(dst, result, delimiter=',')

            # read the generate output
            # based on that determine sleep and number of bytes in output file
            end = time.time()
            runtime_stat = {
                "task_name" : task_name,
                "start" : start,
                "end" : end
            }
            log.warning(json.dumps(runtime_stat))
            for i in range(num_inputs):
                q.task_done()



    log.error("ERROR: should never reach this")


# Run by execution profiler
def profile_execution(task_name):
    q = queue.Queue()
    input_dir = f"{APP_DIR}/sample_inputs/"
    output_dir = f"{APP_DIR}/sample_outputs/"

    # manually add the src (parent) and dst (this task) prefix to the filename
    # here to illustrate how Jupiter will enact this under the hood. the actual
    # src (or parent) is not needed for profiling execution so we fake it here.


    os.makedirs(output_dir, exist_ok=True)
    t = threading.Thread(target=task, args=(q, input_dir, output_dir, task_name))
    t.start()

    for file in os.listdir(input_dir):
        try:
            src_task, dst_task, base_fname = file.split("_", maxsplit=3)
        except ValueError:
            # file is not in the correct format
            continue

        if dst_task.startswith(task_name):
            q.put(file)
    q.join()

    # execution profiler needs the name of ouput files to analyze sizes
    output_files = []
    for file in os.listdir(output_dir):
        if file.startswith(task_name):
            output_files.append(file)

    return output_dir, output_files


if __name__ == '__main__':
    # Testing Only
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    for dag_task in app_config.get_dag_tasks():
        if dag_task['base_script'] == __file__:
            log.debug(profile_execution(dag_task['name']))