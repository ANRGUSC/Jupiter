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

'''
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
'''

def gen_stream_fixed_set_data(task_name,interval,num_images,data_path,original_data_path):
    index = task_name.strip('datasource') # take the task_name index number by stripping out the 'datasource' prefix
    list_files = os.listdir(original_data_path)
    '''
    example output of list_files:
    ['home_master_416imgleopard.JPEG', 'home_master_8166imgwhitewolf.JPEG', 'home_master_695imgmongoose.JPEG', 'home_master_985imgwhitewolf.JPEG', 'home_master_423imgmongoose.JPEG', 'home_master_5191imgwhitewolf.JPEG', 'home_master_725imgmongoose.JPEG', 'home_master_76imgfireengine.JPEG', 'home_master_1204imgkitfox.JPEG', 'home_master_1104imgkitfox.JPEG', 'home_master_6007imgpersiancat.JPEG', 'home_master_493imgleopard.JPEG', 'home_master_6001imgpersiancat.JPEG', 'home_master_6008imgpersiancat.JPEG', 'home_master_920imgtiger.JPEG', 'home_master_251imgleopard.JPEG', 'home_master_5imgleopard.JPEG', 'home_master_9782imgtiger.JPEG', 'home_master_6003imgpersiancat.JPEG', 'home_master_1082imgwhitewolf.JPEG', 'home_master_7002imgleopard.JPEG', 'home_master_511imgtiger.JPEG', 'home_master_883imgschoolbus.JPEG', 'home_master_1009imgfireengine.JPEG', 'home_master_1130imgtiger.JPEG', 'home_master_1192imgleopard.JPEG', 'home_master_6002imgpersiancat.JPEG', 'home_master_381imgfireengine.JPEG', 'home_master_1078imgtiger.JPEG', 'home_master_942imgtiger.JPEG', 'home_master_426imgtiger.JPEG', 'home_master_1166imgwhitewolf.JPEG', 'home_master_714imgtiger.JPEG', 'home_master_1179imgfireengine.JPEG', 'home_master_936imgkitfox.JPEG', 'home_master_186imgkitfox.JPEG', 'home_master_258imgfireengine.JPEG', 'home_master_729imgtiger.JPEG', 'home_master_1043imgtiger.JPEG', 'home_master_625imgkitfox.JPEG', 'home_master_8000imgmongoose.JPEG', 'home_master_6004imgpersiancat.JPEG', 'home_master_624imgwhitewolf.JPEG', 'home_master_1176imgkitfox.JPEG', 'home_master_334imgkitfox.JPEG', 'home_master_214imgwhitewolf.JPEG', 'home_master_106imgmongoose.JPEG', 'home_master_405imgmongoose.JPEG', 'home_master_1191imgwhitewolf.JPEG', 'home_master_25imgpersiancat.JPEG', 'home_master_282imgleopard.JPEG', 'home_master_9082imgwhitewolf.JPEG', 'home_master_83imgschoolbus.JPEG', 'home_master_674imgfireengine.JPEG', 'home_master_695imgkitfox.JPEG', 'home_master_722imgleopard.JPEG', 'home_master_727imgkitfox.JPEG', 'home_master_154imgpersiancat.JPEG', 'home_master_567imgschoolbus.JPEG', 'home_master_503imgschoolbus.JPEG', 'home_master_749imgschoolbus.JPEG', 'home_master_762imgschoolbus.JPEG', 'home_master_1033imgfireengine.JPEG', 'home_master_1140imgfireengine.JPEG', 'home_master_689imgschoolbus.JPEG', 'home_master_294imgleopard.JPEG', 'home_master_329imgkitfox.JPEG', 'home_master_926imgschoolbus.JPEG', 'home_master_511imgmongoose.JPEG', 'home_master_91imgfireengine.JPEG', 'home_master_131imgwhitewolf.JPEG', 'home_master_430imgfireengine.JPEG', 'home_master_1731imgtiger.JPEG', 'home_master_565imgschoolbus.JPEG', 'home_master_9850imgwhitewolf.JPEG', 'home_master_154imgfireengine.JPEG', 'home_master_6006imgpersiancat.JPEG', 'home_master_116imgmongoose.JPEG', 'home_master_7000imgleopard.JPEG', 'home_master_236imgschoolbus.JPEG', 'home_master_497imgpersiancat.JPEG', 'home_master_42imgwhitewolf.JPEG', 'home_master_8001imgmongoose.JPEG', 'home_master_7003imgleopard.JPEG', 'home_master_1imgfireengine.JPEG', 'home_master_6005imgpersiancat.JPEG', 'home_master_7001imgleopard.JPEG', 'home_master_807imgmongoose.JPEG', 'home_master_801imgmongoose.JPEG', 'home_master_185imgkitfox.JPEG', 'home_master_923imgschoolbus.JPEG', 'home_master_1163imgschoolbus.JPEG', 'home_master_8005imgmongoose.JPEG', 'home_master_499imgkitfox.JPEG', 'home_master_6009imgpersiancat.JPEG', 'home_master_1030imgtiger.JPEG']
    '''
    # group images by class
    list_files = sorted(list_files, key=lambda x: x.split('_')[2].split('img')[1])
    # in a while loop send images starting with list item (len(list_files) % int(index))
    for i in range(0,num_images):
        #time.sleep(interval + int(index)) # add offset to this interval based on task name (eg task 200 starts at 60 seconds)
        time.sleep(interval)
        #offset = int(index) % len(list_files)
        offset = 0
        filename = list_files[(offset + i) % len(list_files)]
        source = os.path.join(original_data_path,filename)
        new_filename = filename.split('_')[0] + "_" + filename.split('_')[1] + "_" + ''.join(random.choice(string.digits) for _ in range(8)) + "img" + filename.split('_')[2].split('img')[1]
        destination = os.path.join(data_path,new_filename)
        shutil.copyfile(source, destination)
        ts = time.time()
        show_run_stats(task_name,'new_file_datasource',new_filename)


# Run by dispatcher (e.g. CIRCE). Custom tasks are unable to receive files
# even though a queue is setup. Custom tasks can, however, send files to any
# DAG task.
def task(q, pathin, pathout, task_name):
    #class_num = task_name.split('datasource')[1:]
    #class_name = ccdag.CLASSLIST[int(class_num)-1]
    original_data_path = '/jupiter/build/app_specific_files/data/datasource/'
    #original_data_path = '/jupiter/build/app_specific_files/data/datasource1'
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
