"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import paramiko
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
from multiprocessing import Process
from readconfig import read_config
from socket import gethostbyname, gaierror, error

from watchdog.events import PatternMatchingEventHandler
import multiprocessing
from flask import Flask, request
from collections import defaultdict

from os import path
import configparser

##
## Load all the confuguration
##
INI_PATH = '/jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
username    = config['AUTH']['USERNAME']
password    = config['AUTH']['PASSWORD']
ssh_port    = int(config['PORT']['SSH_SVC'])
num_retries = int(config['OTHER']['SSH_RETRY_NUM'])


# End-to-end metrics
start_times = []
end_times = []
exec_times = []
count = 0

app = Flask(__name__)

# Per task times
start_time = defaultdict(list)
end_time = defaultdict(list)


@app.route('/recv_monitor_data')
def recv_mapping():
    global start_time
    global end_time

    try:
        worker_node = request.args.get('work_node')
        msg = request.args.get('msg')
        ts = time.time()

        # print("Received flask message:", worker_node, msg, ts)

        if msg == 'start':
            start_time[worker_node].append(ts)
        else:
            end_time[worker_node].append(ts)
            print(worker_node + " takes time:" + str(end_time[worker_node][-1] - start_time[worker_node][-1]))
            if worker_node == "globalfusion":
                # Per task stats:
                print("Start time stats:", start_time)
                print("End time stats:", end_time)

    except Exception as e:
        print("Bad reception or failed processing in Flask")
        print(e)
        return "not ok"
    return "ok"


class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)


class MyHandler(PatternMatchingEventHandler):


    def process(self, event):
        global start_times
        global end_times
        global exec_times
        global count
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        if event.event_type == 'created':
            print(event.src_path, event.event_type)  # print now only for degug
            end_times.append(time.time())
            print("ending time is: ", end_times)

            exec_times.append(end_times[count] - start_times[count])

            print("execution time is: ", exec_times)
            # global count
            count+=1

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


class Watcher:
    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'input/')

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()

class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':

            print("Received file as input - %s." % event.src_path)

            start_times.append(time.time())
            print("start time is: ", start_times)
            new_file_name = os.path.split(event.src_path)[-1]


            #This part should be optimized to avoid hardcoding IP, user and password
            #of the first task node
            IP = os.environ['CHILD_NODES_IPS']
            #IP= 'localpro'

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            retry = 0
            # num_retries = 30
            print("Starting the connection")
            while retry < num_retries:
                try:
                    ssh.connect(IP, username=username, password=password, port=ssh_port)
                    sftp = ssh.open_sftp()
                    sftp.put(event.src_path, os.path.join('/centralized_scheduler', 'input', new_file_name))
                    sftp.close()
                    break
                except:
                    print('SSH connection refused or file transfer failed, will retry in 2 seconds')
                    time.sleep(2)
                    retry += 1

            ssh.close()


if __name__ == '__main__':

    path1 = 'configuration.txt'
    path2 = 'nodes.txt'
    dag_info = read_config(path1,path2)

    #get DAG and home machine info
    first_task = dag_info[0]
    dag = dag_info[1]
    hosts=dag_info[2]

    print("TASK1: ", dag_info[0])
    print("DAG: ", dag_info[1])
    print("HOSTS: ", dag_info[2])

    #monitor INPUT folder for the incoming files
    w = Watcher()
    w.run()

    web_server = MonitorRecv()
    web_server.start()

    print("Starting the output monitoring system:")
    observer = Observer()
    observer.schedule(MyHandler(), path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'output/'))
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()