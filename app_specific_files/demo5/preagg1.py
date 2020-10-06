import os
import shutil
import sys
import queue
import threading
import logging
import glob
import time
import json
import ccdag


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
app_config = app_config_parser.AppConfig(APP_DIR, "demo5")

#task config information
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
config = configparser.ConfigParser()
config.read(JUPITER_CONFIG_INI_PATH)

FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])

classids = np.arange(0,len(ccdag.classlist),1)
classmap = dict(zip(ccdag.classlist, classids))


# Run by dispatcher (e.g. CIRCE). Use task_name to differentiate the tasks by
# name to reuse one base task file.
def task(q, pathin, pathout, task_name):
    children = app_config.child_tasks(task_name)
    classnum = task_name.split('preagg')[1]

    while True:
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

        # PREAGG code


        job_id = src.split('jobid')[1]
        print(job_id)
        
        # job_id = int(job_id)
        
        
        hdr = {
                'Content-Type': 'application/json',
                'Authorization': None 
                                    }
        # the message of requesting dictionary
        # payload = {
        #     'job_id': job_id,
        #     'filename': filelist[0]
        # }
        payload = {
            'class_image': int(classnum),
            'job_id': job_id,
            'filename': filelist[0]
        }
        
        # address of flask server for class1 is 0.0.0.0:5000 and "post-dict" is for requesting dictionary 
        try:
            # url = "http://0.0.0.0:5000/post-dict"
            global_info_ip = os.environ['GLOBAL_IP']
            url = "http://%s:%s/post-dict"%(global_info_ip,str(FLASK_SVC))
            print(url)
            # request of dictionary of received results
            response =  requests.post(url, headers = hdr,data = json.dumps(payload))
            job_dict = response.json()
            print(job_dict)
        except Exception as e:
            print('Possibly running on the execution profiler')
            if ccdag.CODING_PART2 == 1:
                sample1 = [f for f in listdir(pathout) if f.startswith('score2a_preagg2_job2')]
                sample2 = [f for f in listdir(pathout) if f.startswith('score2b_preagg2_job2')]
                job_dict = {'2':[sample1[0],sample2[0]]}
            else:
                sample1 = [f for f in listdir(pathout) if f.startswith('score2a_preagg2_job2')]
                sample2 = [f for f in listdir(pathout) if f.startswith('score2b_preagg2_job2')]
                sample3 = [f for f in listdir(pathout) if f.startswith('score2c_preagg2_job2')]
                job_dict = {'2':[sample1[0],sample2[0],sample3[0]]}
            
        #Parameters
        M = 2 # Number of data-batches
        N = 3 # Number of workers
        
        if ccdag.CODING_PART2: #Coding Version
            #Check if number of received results for the same job is equal to M
            if len(job_dict[job_id]) == M:
                print('Receive enough results for job '+job_id)
                for i in range(M):
                    
                    En_Image_Batch = np.loadtxt(os.path.join(pathin, (job_dict[job_id])[i]), delimiter=',')
                    job = 'job'+str(job_id)
                    dst_task = children # only 1 children
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{job}_{base_fname}")
                    print(dst)
                    # destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'.csv')
                    #destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'_'+filesuffixs+'.log')
                    np.savetxt(dst, En_Image_Batch, delimiter=',')
                
            else:
                print('Not receive enough results for job '+job_id)

            
            return outlist
        
        else:
            #Check if number of received results for the same job is equal to N
            if len(job_dict[job_id]) == N:
                print('Receive enough results for job '+job_id)
                for i in range(N):
                    En_Image_Batch = np.loadtxt(os.path.join(pathin, (job_dict[job_id])[i]), delimiter=',')
                    job = 'job'+str(job_id)
                    dst_task = children # only 1 children
                    dst = os.path.join(pathout, f"{task_name}_{dst_task}_{job}_{base_fname}")
                    print(dst)
                    # destination = os.path.join(pathout,'preagg'+classnum+'_lccdec'+classnum+'_'+(job_dict[job_id])[i].partition('_')[0]+'_job'+job_id+'_'+filesuffixs+'.log')
                    np.savetxt(dst, En_Image_Batch, delimiter=',')
                    
            else:
                print('Not receive enough results for job '+job_id)

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