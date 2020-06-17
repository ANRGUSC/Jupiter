# Bunch of import statements
import os
import shutil
from pathlib import Path
from os import listdir
import logging
import urllib

from datetime import datetime
global circe_home_ip, circe_home_ip_port, taskname
global logging
logging.basicConfig(level = logging.DEBUG)

taskname = Path(__file__).stem
classnum = taskname.split('storeclass')[1]

global FLASK_DOCKER, FLASK_SVC, num_retries, ssh_port, username, password, CODING_PART1
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
ssh_port    = int(config['PORT']['SSH_SVC'])
username    = config['AUTH']['USERNAME']
password    = config['AUTH']['PASSWORD']

def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

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

def send_runtime_stats(action, file_names):
    t = datetime.now()
    ts = unix_time(t)
    for i in range(0,len(file_names)):
        file_name = file_names[i]
        new_file = os.path.split(file_name)[-1]
        original_name = new_file.split('.')[0]
        logging.debug(original_name)
        tmp_name = original_name.split('_')[-1]
        temp_name= tmp_name+'.JPEG'
        runtime_info = action +' '+ temp_name+ ' '+str(ts)
        send_runtime_profile(runtime_info)

"""
Task for node that stores classified images belonding to it's assigned class.
"""
def task(file_, pathin, pathout):
    file_ = [file_] if isinstance(file_, str) else file_

    send_runtime_stats('rt_enter_task', file_)

    out_list = []
    for i, f in enumerate(file_):
        source = os.path.join(pathin, f) 
        # file_split = file_.split("prefix_")[1]
        destination = os.path.join(pathout, "storeclass"+classnum+"_" + f)
        print(source)
        print(destination)
        try: 
            shutil.copyfile(source, destination)
            out_list.append(destination)
        except: 
            print("ERROR while copying file in store_class_task.py")

    send_runtime_stats('rt_finish_task', out_list)
    return out_list

def main():
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    # filelist = (f for f in listdir(outpath) if f.startswith('resnet'))
    filelist = [f for f in listdir(outpath) if taskname in f]
    outfile = task(filelist, outpath, outpath)
    return outfile
	
