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

app = Flask(__name__)

start_times = dict()
end_times = dict()
exec_times = dict()

def gen_stream_data(interval,data_path):
    while True:
        for i in range(0,interval):
            time.sleep(1)
        print('--- Generate new file')
        bash_script = os.path.join(os.getcwd(),'generate_random_files')
        bash_script = bash_script+' '+os.environ['SELF_NAME']
        proc = subprocess.Popen(bash_script, shell = True, stdout = subprocess.PIPE)
        

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
            print('data transfer complete\n')
            break
        except Exception as e:
            print('SSH Connection refused or File transfer failed, will retry in 2 seconds')
            print(e)
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

        print("Received file as input - %s." % event.pathname)  


        inputfile = event.pathname.split('/')[-1]
        t = time.time()
        start_times[inputfile] = t
        new_file_name = os.path.split(event.pathname)[-1]

        ID = os.environ['CHILD_NODES']
        source = event.pathname
        destination = os.path.join('/centralized_scheduler', 'input', new_file_name)

        send_monitor_data(inputfile,'input',t)

        transfer_data(ID,username, password,source, destination)

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
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
        print("Sending message to flask server on home FAILED!!!")
        print(e)
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
    
    print('Starting to generate the streaming files')
    interval = 60
    data_path = "generated_stream"
    _thread.start_new_thread(gen_stream_data,(interval,data_path,))  

    # watch manager
    wm = pyinotify.WatchManager()
    input_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'generated_stream/')
    wm.add_watch(input_folder, pyinotify.ALL_EVENTS, rec=True)
    print('starting the input monitoring process\n')
    eh = Handler()
    notifier = pyinotify.Notifier(wm, eh)
    notifier.loop()

 

if __name__ == '__main__':
    main()    
