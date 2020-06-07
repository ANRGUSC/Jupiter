__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"
"""
    Streaming data generator
"""
import time
import os
import subprocess
import pyinotify
import paramiko
from scp import SCPClient
import _thread
from multiprocessing import Process
import multiprocessing
from flask import Flask, request
import configparser
import urllib
import logging
import random
import shutil

logging.basicConfig(level = logging.DEBUG)

app = Flask(__name__)

start_times = dict()
end_times = dict()
exec_times = dict()

def find_next_file(local_folder):
    list_files = os.listdir(local_folder)
    current_idx = random.randint(0 , len(list_files)-1)
    return list_files[current_idx]

def gen_stream_data(interval,data_path,original_data_path):
    while True:
        for i in range(0,interval):
            time.sleep(1)
        logging.debug('--- Copy new file')
        filename = find_next_file(original_data_path)
        source = os.path.join(original_data_path,filename)
        destination = os.path.join(data_path,filename)
        shutil.copyfile(source, destination)

def gen_stream_fixed_data(interval,num_images,data_path,original_data_path):
    for i in range(0,num_images):
        time.sleep(interval)
        logging.debug('--- Copy new file')
        filename = find_next_file(original_data_path)
        source = os.path.join(original_data_path,filename)
        destination = os.path.join(data_path,filename)
        shutil.copyfile(source, destination)

        

def transfer_data_scp(ID,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        IP (str): destination ID
        user (str): username
        pword (str): password
        source (str): source file path
        destination (str): destination file path
    """
    #Keep retrying in case the containers are still building/booting up on
    #the child nodes.
    retry = 0
    ts = -1
    while retry < num_retries:
        try:
            nodeIP = combined_ip_map[ID]
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, nodeIP, destination)
            os.system(cmd)
            logging.debug('data transfer complete\n')
            break
        except Exception as e:
            logging.debug('SSH Connection refused or File transfer failed, will retry in 2 seconds')
            logging.debug(e)
            time.sleep(2)
            retry += 1


def transfer_data(ID,user,pword,source, destination):
    """Transfer data with given parameters
    
    Args:
        IP (str): destination ID 
        user (str): destination username
        pword (str): destination password
        source (str): source file path
        destination (str): destination file path
    """
    msg = 'Transfer to ID: %s , username: %s , password: %s, source path: %s , destination path: %s'%(ID,user,pword,source, destination)
    

    if TRANSFER == 0:
        return transfer_data_scp(ID,user,pword,source, destination)

    return transfer_data_scp(ID,user,pword,source, destination) #defaul

class Handler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        """On every node, whenever there is scheduling information sent from the central network profiler:
            - Connect the database
            - Scheduling measurement procedure
            - Scheduling regression procedure
            - Start the schedulers
        
        Args:
            event (ProcessEvent): a new file is created
        """

        logging.debug("Received file as input - %s." % event.pathname)  


        inputfile = event.pathname.split('/')[-1]
        t = time.time()
        start_times[inputfile] = t
        new_file_name = os.path.split(event.pathname)[-1]

        ID = os.environ['CHILD_NODES']
        source = event.pathname
        destination = os.path.join('/centralized_scheduler/input', new_file_name)

        send_monitor_data(inputfile,'input',t)

        transfer_data(ID,username, password,source, destination)

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        logging.debug("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)


def send_monitor_data(filename,filetype,ts):
    """
    Sending message to flask server on home

    Args:
        msg (str): the message to be sent

    Returns:
        str: the message if successful, "not ok" otherwise.

    Raises:
        Exception: if sending message to flask server on home is failed
    """
    try:
        url = "http://" + home_node_host_port + "/recv_monitor_datasource"
        params = {'filename': filename, "filetype": filetype,"time":ts}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        logging.debug("Sending message to flask server on home FAILED!!!")
        logging.debug(e)
        return "not ok"
    return res

def main():
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global FLASK_SVC,FLASK_DOCKER,username, password, TRANSFER,num_retries,ssh_port
    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    TRANSFER = int(config['CONFIG']['TRANSFER'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    ssh_port    = int(config['PORT']['SSH_SVC'])
    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
    STREAM_INTERVAL = int(config['PORT']['STREAM_INTERVAL'])

    global current_idx
    current_idx = 0

    global combined_ip_map
    combined_ip_map = dict()
    combined_ip_map[os.environ['CHILD_NODES']]= os.environ['CHILD_NODES_IPS']

    global home_node_host_port
    home_node_host_port = os.environ['HOME_NODE'] + ":" + str(FLASK_SVC)

    global all_nodes,all_nodes_ips
    all_nodes = os.environ['ALL_NODES'].split(' ')
    all_nodes_ips = os.environ['ALL_NODES_IPS'].split(' ')


    web_server = MonitorRecv()
    web_server.start()
    
    logging.debug('Starting to generate the streaming files')
    # interval = 5
    data_path = "generated_stream"
    original_data_path = "data"
    # Generate streaming data
    # _thread.start_new_thread(gen_stream_data,(interval,data_path,original_data_path))  

    # Generate fixed number of images
    num = 100
    _thread.start_new_thread(gen_stream_fixed_data,(STREAM_INTERVAL,num,data_path,original_data_path)) 

    # watch manager
    wm = pyinotify.WatchManager()
    input_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'generated_stream/')
    wm.add_watch(input_folder, pyinotify.ALL_EVENTS, rec=True)
    logging.debug('starting the input monitoring process\n')
    eh = Handler()
    notifier = pyinotify.Notifier(wm, eh)
    notifier.loop()

 

if __name__ == '__main__':
    main()    
