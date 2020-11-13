import os
import sys
import queue
import threading
import logging
import time
import string
import random
import _thread
import shutil
from ccdag_utils import *
import json


logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
    from jupiter_utils import app_config_parser
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../core/")
    from jupiter_utils import app_config_parser

import ccdag


# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)


def gen_stream_fixed_set_data(task_name,interval,num_images,data_path,original_data_path):
    list_files = os.listdir(original_data_path)
    for i in range(0,num_images):
        time.sleep(interval)
        filename = list_files[i]
        source = os.path.join(original_data_path,filename)
        destination = os.path.join(data_path,filename)
        shutil.copyfile(source, destination)
        ts = time.time()
        show_run_stats(task_name,'new_file_datasource',filename)



# Run by dispatcher (e.g. CIRCE). Custom tasks are unable to receive files
# even though a queue is setup. Custom tasks can, however, send files to any
# DAG task.
def task(q, pathin, pathout, task_name):
    #class_num = task_name.split('datasource')[1:]
    #class_name = ccdag.classlist[int(class_num)-1]
    original_data_path = '/jupiter/build/app_specific_files/data/%s'%(task_name)
    data_path = pathout

    log.info(f"Starting non-DAG task {task_name}")
    children = app_config.child_tasks(task_name)
    log.info(f"My children are {children}")

    time.sleep(300) #waiting for all the pods to be ready
    gen_stream_fixed_set_data(task_name,ccdag.STREAM_INTERVAL,ccdag.NUM_IMAGES,data_path,original_data_path)

    while True:
        time.sleep(999)

    log.error("ERROR: should never reach this")


if __name__ == '__main__':
    # Testing Only
    q = queue.Queue()
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    t = threading.Thread(target=task, args=(q, "./", "./", "test"))
    t.start()
