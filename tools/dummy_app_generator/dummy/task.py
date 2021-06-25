import os
import shutil
import sys
import queue
import threading
import logging
import glob
import json
import time
import math
import random



logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../core/")
    
from jupiter_utils import app_config_parser
from jupiter_utils import parser
from jupiter_utils.parser import *

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)


# Run by dispatcher (e.g. CIRCE). Use task_name to differentiate the tasks by
# name to reuse one base task file.
def task(q, pathin, pathout, task_name):
    children = app_config.child_tasks(task_name)
    cnt = 0
    while True:
        input_file = q.get()
        show_run_stats(task_name,'queue_start_process',input_file)
        start = time.time()
        src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
        log.info(f"{task_name}: file rcvd from {src_task}")
        if 'home' not in children:
            log.info('The children node is not home node!!!!!')
            ## Read parameters from file
            f = open(f"{APP_DIR}/config.txt", 'r')
            total_info = f.read().splitlines()
            f.close()
            comm = dict()
            comp = 0
            for line in total_info:
                src = line.strip().split(' ')[0]
                if src!=task_name:
                    continue
                comp = float(line.strip().split(' ')[1])
                dest_info = line.strip().split(' ')[2:]
                if len(dest_info)>0:
                    dest = [x.split('-')[0] for x in dest_info]
                    fs = [float(x.split('-')[1]) for x in dest_info]
                    for idx,d in enumerate(dest):
                        comm[d] = int(fs[idx])

            print('Computation {}'.format(comp))
            print('Communication {}'.format(comm))
            print('Destination {}'.format(dest))

            ## Perform computation task
            while time.time() < comp:
                1+1
            ## Perform communication task
            for idx,x in enumerate(dest):
                src = os.path.join(pathin, input_file)
                dst_task = dest[idx]  # round robin selection
                dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
                #generate required file with specified file size following config.txt at the destination folder
                bash_script=f'{APP_DIR}/generate_random_files.sh'+' '+dst+' '+str(comm[dst_task])
                print('Bash_script : {}'.format(bash_script))
                os.system(bash_script)
                show_run_stats(task_name,'queue_end_process',f"{task_name}_{dst_task}_{base_fname}")
        else:
            log.info('This is the last task. The children node is home node!!!!!')
            dst = os.path.join(pathout, f"{task_name}_home_{base_fname}")
            with open(dst, "w") as f:
                f.write("This is the last task already. Doing no computation & communication task, just create a fake output file...")

            show_run_stats(task_name,'queue_end_process',f"{task_name}_home_{base_fname}")
        
        cnt += 1
        
        q.task_done()

    log.error("ERROR: should never reach this")
        
# Run by execution profiler
def profile_execution(task_name):
    q = queue.Queue()
    input_dir = f"{APP_DIR}/sample_inputs/"
    output_dir = f"{APP_DIR}/sample_outputs/"

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
            shutil.copy('{}/{}'.format(output_dir,file),'{}/{}'.format(input_dir,file))
    print("Output files : {}".format(output_files))


    return output_dir, output_files


if __name__ == '__main__':
    # Testing Only
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    for dag_task in app_config.get_dag_tasks():
        if dag_task['base_script'] == __file__:
            log.debug(profile_execution(dag_task['name']))