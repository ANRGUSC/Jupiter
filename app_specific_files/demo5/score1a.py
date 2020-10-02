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

global SLEEP_TIME, STRAGGLER_THRESHOLD
SLEEP_TIME   = int(config['OTHER']['SLEEP_TIME'])
STRAGGLER_THRESHOLD   = float(config['OTHER']['STRAGGLER_THRESHOLD'])
classlist = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard', 'lion',  'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']


# Similarity score (zero-normalized cross correlation)
def score (En_Image_Batch, Ref_Images):
    K, F = Ref_Images.shape
    L, F = En_Image_Batch.shape
    ref_scores = np.zeros((K,L)) # K * length(vector)
    for i in range(K):
        for j in range(L):
            ref_scores[i,j] = np.mean(np.correlate(En_Image_Batch[j], Ref_Images[i]))
    return ref_scores


# Run by dispatcher (e.g. CIRCE). Use task_name to differentiate the tasks by
# name to reuse one base task file.
def task(q, pathin, pathout, task_name):
    children = app_config.child_tasks(task_name)

    class_num = taskname.split('score')[1][0]
    class_name = classlist[int(class_num)-1]

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


    job_id = filelist[0].split('.csv')[0].split('_')[-2].split('job')[1]
    
    filesuffixs = filelist[0].split('.csv')[0].split('_')[-1]
    

    #Worker ID: a,b,c...
    worker_id = task_name[-1]
    print(worker_id)
    #worker_id = 'a'
    
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
    filelist_ref = [class_name+str(i+1)+'.JPEG' for i in range(20,30)]  # to be defined in advance
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
    if (random.random() > STRAGGLER_THRESHOLD) and (worker_id=='a'):
        print(classnum)
        print("Sleeping")
        time.sleep(SLEEP_TIME) #>=2 
    
    
    # Read Encoded data-batch   
    En_Image_Batch = np.loadtxt(os.path.join(pathin, filelist[0]), delimiter=',')
    
    
    # Compute Scores of ref images and En_Images
    sc = score(En_Image_Batch, Ref_Images)
    job = 'job'+str(job_id)
    dst_task = children # only 1 children
    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{job}_{base_fname}")
    np.savetxt(dst, sc, delimiter=',')
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