# Bunch of import statements
import os
import shutil
from pathlib import Path
from os import listdir
import logging
import urllib
import configparser
import time

from datetime import datetime
global circe_home_ip, circe_home_ip_port, taskname
global logging

logging.basicConfig(level = logging.DEBUG)

INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

taskname = Path(__file__).stem
classnum = taskname.split('storeclass')[1]

global FLASK_DOCKER, FLASK_SVC, num_retries, ssh_port, username, password, CODING_PART1
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
ssh_port    = int(config['PORT']['SSH_SVC'])
username    = config['AUTH']['USERNAME']
password    = config['AUTH']['PASSWORD']

def send_runtime_profile(msg):
    """
    Sending runtime profiling information to flask server on home

    Args:
        msg (str): the message to be sent

    Returns:
        str: the message if successful, "not ok" otherwise.

    Raises:
        Exception: if sending message to flask server on home is failed
    """
    try:
        logging.debug('Sending runtime stats')
        logging.debug(msg)
        circe_home_ip_port = os.environ['HOME_NODE'] + ":" + str(FLASK_SVC)
        url = "http://" + circe_home_ip_port + "/recv_runtime_profile"
        params = {'msg': msg, "work_node": taskname}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        logging.debug("Sending runtime profiling info to flask server on home FAILED!!!")
        logging.debug(e)
        return "not ok"
    return res

def send_runtime_stats(action, file_name,from_task):
    ts = time.time()
    new_file = os.path.split(file_name)[-1]
    original_name = new_file.split('.')[0]
    logging.debug(original_name)
    tmp_name = original_name.split('_')[-1]
    temp_name= tmp_name+'.JPEG'
    runtime_info = action +' '+ from_task+' '+ temp_name+ ' '+str(ts) 
    send_runtime_profile(runtime_info)

"""
Task for node that stores classified images belonding to it's assigned class.
"""
def task(file_, pathin, pathout):
    file_ = [file_] if isinstance(file_, str) else file_
    for f in file_:
        from_task = os.path.split(f)[-1].split('.')[0].split('_')[0]
        send_runtime_stats('rt_enter_task', f,from_task)

    out_list = []
    for i, f in enumerate(file_):
        source = os.path.join(pathin, f) 
        from_task = os.path.split(f)[-1].split('.')[0].split('_')[0]
        # file_split = file_.split("prefix_")[1]
        destination = os.path.join(pathout, "storeclass"+classnum+"_" + f)
        print(source)
        print(destination)
        try: 
            shutil.copyfile(source, destination)
            out_list.append(destination)
            send_runtime_stats('rt_finish_task', destination,from_task)
        except: 
            print("ERROR while copying file in store_class_task.py")

    
    return out_list

def main():
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    # filelist = (f for f in listdir(outpath) if f.startswith('resnet'))
    filelist = [f for f in listdir(outpath) if taskname in f]
    outfile = task(filelist, outpath, outpath)
    return outfile
	
