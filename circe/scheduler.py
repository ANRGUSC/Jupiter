#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on the scheduler node of CIRCE. 

"""

__author__ = "Aleksandra Knezevic,Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen,  Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import paramiko
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import json
from multiprocessing import Process
from readconfig import read_config
from socket import gethostbyname, gaierror, error

from watchdog.events import PatternMatchingEventHandler
import multiprocessing
from flask import Flask, request
from collections import defaultdict

from os import path
import configparser




# End-to-end metrics
start_times = []
end_times = []
exec_times = []
count = 0

app = Flask(__name__)

# Per task times
start_time = defaultdict(list)
end_time = defaultdict(list)

rt_enter_time = defaultdict(list)
rt_exec_time = defaultdict(list)
rt_finish_time = defaultdict(list)

#@app.route('/recv_monitor_data')
def recv_mapping():
    """

    Receiving run-time profiling information from WAVE/HEFT for every task (task name, start time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """

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
app.add_url_rule('/recv_monitor_data', 'recv_mapping', recv_mapping)

def return_output_files():
    """
    Return number of output files
    
    Returns:
        int: number of output files
    """
    num_files = len(os.listdir("output/"))
    print("Recieved request for number of output files. Current done:", num_files)
    return json.dumps(num_files)
app.add_url_rule('/', 'return_output_files', return_output_files)

def recv_runtime_profile():
    """

    Receiving run-time profiling information for every task (task name, start time stats, waiting time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """

    global rt_enter_time
    global rt_exec_time
    global rt_finish_time

    try:
        worker_node = request.args.get('work_node')
        msg = request.args.get('msg').split()
        

        print("Received flask message:", worker_node, msg[0],msg[1], msg[2])

        if msg[0] == 'rt_enter':
            rt_enter_time[(worker_node,msg[1])] = float(msg[2])
        elif msg[0] == 'rt_exec' :
            rt_exec_time[(worker_node,msg[1])] = float(msg[2])
        else: #rt_finish
            rt_finish_time[(worker_node,msg[1])] = float(msg[2])

            print('----------------------------')
            print("Worker node: "+ worker_node)
            print("Input file : "+ msg[1])
            print("Total duration time:" + str(rt_finish_time[(worker_node,msg[1])] - rt_enter_time[(worker_node,msg[1])]))
            print("Waiting time:" + str(rt_exec_time[(worker_node,msg[1])] - rt_enter_time[(worker_node,msg[1])]))
            print(worker_node + " execution time:" + str(rt_finish_time[(worker_node,msg[1])] - rt_exec_time[(worker_node,msg[1])]))
            
            print('----------------------------')  
            if worker_node == "globalfusion":
                # Per task stats:
                print('********************************************') 
                print("Runtime profiling info:")
                """
                    - Worker node: task name
                    - Input file: input files
                    - Enter time: time the input file enter the queue
                    - Execute time: time the input file is processed
                    - Finish time: time the output file is generated
                    - Elapse time: total time since the input file is created till the output file is created
                    - Duration time: total execution time of the task
                    - Waiting time: total time since the input file is created till it is processed
                """
                
                s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Task_name','local_input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time')
                print(s)
                for k, v in rt_enter_time.items():
                    worker, file = k
                    if k in rt_finish_time:
                        elapse = rt_finish_time[k]-v
                        duration = rt_finish_time[k]-rt_exec_time[k]
                        waiting = rt_exec_time[k]-v
                        s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(worker, file, v, rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting))
                        print(s)
                print('********************************************')

                
    except Exception as e:
        print("Bad reception or failed processing in Flask for runtime profiling")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_runtime_profile', 'recv_runtime_profile', recv_runtime_profile)

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)


class MyHandler(PatternMatchingEventHandler):
    """
    Handling the event when there is a new file generated in ``OUTPUT`` folder
    """

    def process(self, event):
        """
        Log the time the file is created and calculate the execution time whenever there is an event.
        
        Args:
            event: event to be watched for the ``OUTPUT`` folder
        """

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
        """
        Monitoring ``INPUT`` folder for the incoming files.
        
        At the moment you have to manually place input files into the ``INPUT`` folder (which is under ``centralized_scheduler_with_task_profiler\``):
        
            .. code-block:: bash
        
                mv 1botnet.ipsum input/
        
        Once the file is there, it sends the file to the node performing the first task.
        """

        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()

class Handler(FileSystemEventHandler):
    """
        Handling the event when there is a new file generated in ``INPUT`` folder
    """

    @staticmethod
    def on_any_event(event):
        """
        Whenever there is a new input file in ``INPUT`` folder, the function:

        - Log the time the file is created

        - Start the connection to the first scheduled node

        - Copy the newly created file to the ``INPUT`` folder of the first scheduled node
        
        Args:
            event (FileSystemEventHandler): monitored event
        """

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

def main():
    """
        -   Read configurations (DAG info, node info) from ``nodes.txt`` and ``configuration.txt``
        -   Monitor ``INPUT`` folder for the incoming files
        -   Whenever there is a new file showing up in ``INPUT`` folder, copy the file to the ``INPUT`` folder of the first scheduled node.
        -   Collect execution profiling information from the system.
    """

    ##
    ## Load all the confuguration
    ##
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global FLASK_DOCKER, username, password, ssh_port, num_retries

    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])


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


    
    
if __name__ == '__main__':

    main()