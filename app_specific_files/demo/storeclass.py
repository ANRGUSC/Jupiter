import os
import shutil
import sys
import queue
import threading
import logging
import glob
import time
import json
from ccdag_utils import *

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
    sys.path.append("/jupiter/build/app_specific_files/")
    from jupiter_utils import app_config_parser
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../core/")
    from jupiter_utils import app_config_parser



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

    while True:
        if q.qsize()>0:
            input_file = q.get()
            show_run_stats(task_name,'queue_start_process',input_file)
            src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
            #show_run_stats(task_name,'queue_start_process',input_file,src_task)
            log.debug(f"{task_name}: file rcvd from {src_task} : {base_fname}")

            # Process the file (this example just passes along the file as-is)
            # Once a file is copied to the `pathout` folder, CIRCE will inspect the
            # filename and pass the file to the next task.
            src = os.path.join(pathin, input_file)
            dst_task = children[0] # only 1 child
            dst = os.path.join(pathout, f"{task_name}_{dst_task}_{base_fname}")
            shutil.copyfile(src, dst)

            # read the generate output
            # based on that determine sleep and number of bytes in output file
            show_run_stats(task_name,'queue_end_process',f"{task_name}_{dst_task}_{base_fname}")
            #show_run_stats(task_name,'queue_end_process',f"{task_name}_{dst_task}_{base_fname}",src_task)
            #q.task_done()
        else:
            log.debug('Not enough files')
            time.sleep(1)

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

    return output_dir, output_files


if __name__ == '__main__':
    # Testing Only
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    for dag_task in app_config.get_dag_tasks():
        if dag_task['base_script'] == __file__:
            log.debug(profile_execution(dag_task['name']))