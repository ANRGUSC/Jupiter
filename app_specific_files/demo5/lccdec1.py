import os
import shutil
import sys
import queue
import threading
import logging
import glob
import time
import json


logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
    from jupiter_utils import app_config_parser
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../mulhome_scripts/")
    from jupiter_utils import app_config_parser

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR, "refactor_demo5")

#task config information
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
config = configparser.ConfigParser()
config.read(JUPITER_CONFIG_INI_PATH)


FLAG_PART2 = int(config['OTHER']['FLAG_PART2'])

classlist = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard', 'lion',  'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
classids = np.arange(0,len(classlist),1)
classmap = dict(zip(classlist, classids))

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
    class_num = taskname.split('lccdec')[1]

    input_file = q.get()
    start = time.time()
    src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
    log.info(f"{task_name}: file rcvd from {src_task}")

    # Process the file (this example just passes along the file as-is)
    # Once a file is copied to the `pathout` folder, CIRCE will inspect the
    # filename and pass the file to the next task.
    src = os.path.join(pathin, input_file)
    # dst_task = children[cnt % len(children)]  # round robin selection
    # dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
    # shutil.copyfile(src, dst)

    #LCCDEC CODE
    print(src)
    job_id = src.split('job')[1]
    print(job_id)
   
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
        for j in range(M):
            if j== 0:
                result = results[j]
            else:
                result = np.concatenate((result, results[j]), axis = 0)

        job = 'job'+str(job_id)
        dst_task = children # only 1 children
        dst = os.path.join(pathout, f"{task_name}_{dst_task}_{job}_{base_fname}")
        np.savetxt(dst, result, delimiter=',')

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
        for j in range(M):
            if j== 0:
                result = results[j]
            else:
                result = np.concatenate((result, results[j]), axis = 0)
        dst = os.path.join(pathout, f"{task_name}_{dst_task}_{job}_{base_fname}")
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
    for file in os.listdir(input_dir):
        # skip filse made by other threads when testing locally
        if file.startswith("EXECPROFILER_") is True:
            continue

        # create an input for each child of this task
        for cnt in range(len(app_config.child_tasks(task_name))):
            new = f"{input_dir}/EXECPROFILER{cnt}_{task_name}_{file}"
            shutil.copyfile(os.path.join(input_dir, file), new)

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

    # clean up input files
    files = glob.glob(f"{input_dir}/EXECPROFILER*_{dst_task}*")
    for f in files:
        os.remove(f)

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
        log.debug(profile_execution(dag_task['name']))