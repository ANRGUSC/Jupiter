#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on the scheduler node of CIRCE. 

"""

__author__ = "Aleksandra Knezevic,Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,   Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import paramiko
from scp import SCPClient
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
import numpy as np
from collections import defaultdict
import paho.mqtt.client as mqtt
import jupiter_config

global bottleneck
bottleneck = defaultdict(list)

def tic():
    return time.time()

def toc(t):
    texec = time.time() - t
    print('Execution time is:'+str(texec))
    return texec




# End-to-end metrics
start_times = dict()
end_times = dict()
exec_times = dict()
count = 0

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

# Per task times
start_time = defaultdict(list)
end_time = defaultdict(list)

rt_enter_time = defaultdict(list)
rt_exec_time = defaultdict(list)
rt_finish_time = defaultdict(list)

def demo_help(server,port,topic,msg):
    print('Sending demo')
    print(topic)
    print(msg)
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()

def recv_mapping():
    """

    Receiving run-time profiling information from WAVE/HEFT for every task (task name, start time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """

    global start_time
    global end_time

    try:
        # print('***************************************************')
        # t = tic()
        # print('Receive final runtime profiling')
        worker_node = request.args.get('work_node')
        msg = request.args.get('msg')
        ts = time.time()

        print("Received flask message:", worker_node, msg, ts)
        print(last_tasks)
        if msg == 'start':
            start_time[worker_node].append(ts)
        else:
            end_time[worker_node].append(ts)
            # print(worker_node + " takes time:" + str(end_time[worker_node][-1] - start_time[worker_node][-1]))
            if worker_node in last_tasks:
                # print(worker_node)
            #if worker_node == "globalfusion":
                # Per task stats:
                print("Start time stats:", start_time)
                print("End time stats:", end_time)


        # txec = toc(t)
        # bottleneck['receivefinalruntime'].append(txec)
        # print(np.mean(bottleneck['receivefinalruntime']))
        # print('***************************************************')

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
    # print("Recieved request for number of output files. Current done:", num_files)
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
        

        # print("Received runtime message:", worker_node, msg[0],msg[1], msg[2])
        
        # print(rt_enter_time)
        # print(rt_exec_time)
        # print(rt_finish_time)

        if msg[0] == 'rt_enter':
            rt_enter_time[(worker_node,msg[1])] = float(msg[2])
        elif msg[0] == 'rt_exec' :
            rt_exec_time[(worker_node,msg[1])] = float(msg[2])
        else: #rt_finish
            rt_finish_time[(worker_node,msg[1])] = float(msg[2])
            # print('----------------------------')
            # print("Worker node: "+ worker_node)
            # print("Input file : "+ msg[1])
            # print("Total duration time:" + str(rt_finish_time[(worker_node,msg[1])] - rt_enter_time[(worker_node,msg[1])]))
            # print("Waiting time:" + str(rt_exec_time[(worker_node,msg[1])] - rt_enter_time[(worker_node,msg[1])]))
            # print(worker_node + " execution time:" + str(rt_finish_time[(worker_node,msg[1])] - rt_exec_time[(worker_node,msg[1])]))
            
            # print('----------------------------') 
            #if worker_node == "globalfusion" or "task4" or "task99":
            if worker_node in last_tasks:
                # Per task stats:
                print('********************************************') 
                print("Received final output at home: Runtime profiling info:")
                # print(worker_node)
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
                log_file = open(os.path.join(os.path.dirname(__file__), 'runtime_tasks.txt'), "w")
                s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Task_name','local_input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time')
                # print(s)
                log_file.write(s)
                # print(rt_enter_time)
                for k, v in rt_enter_time.items():
                    worker, file = k
                    # print(worker)
                    # print(file)
                    # print(rt_finish_time)
                    if k in rt_finish_time:
                        elapse = rt_finish_time[k]-v
                        duration = rt_finish_time[k]-rt_exec_time[k]
                        waiting = rt_exec_time[k]-v
                        s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(worker, file, v, rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting))
                        print(s)
                        log_file.write(s)
                        log_file.flush()

                log_file.close()
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

def transfer_data_scp(IP,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        IP (str): destination IP address
        user (str): username
        pword (str): password
        source (str): source file path
        destination (str): destination file path
    """
    #Keep retrying in case the containers are still building/booting up on
    #the child nodes.
    # print('***************************************************')
    # print('Transfer data')
    # t = tic()
    # print(IP)
    retry = 0
    ts = -1
    while retry < num_retries:
        try:
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, IP, destination)
            os.system(cmd)
            print('data transfer complete\n')
            ts = time.time()
            s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home', transfer_type,source,ts)
            runtime_sender_log.write(s)
            runtime_sender_log.flush()
            break
        except:
            print('profiler_worker.txt: SSH Connection refused or File transfer failed, will retry in 2 seconds')
            time.sleep(2)
            retry += 1
    # txec = toc(t)
    # bottleneck['transfer'].append(txec)
    # print(np.mean(bottleneck['transfer']))
    # print('***************************************************')
    if retry == num_retries:
        s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,source,ts)
        runtime_sender_log.write(s)
        runtime_sender_log.flush()

    

def transfer_data(IP,user,pword,source, destination):
    """Transfer data with given parameters
    
    Args:
        IP (str): destination IP 
        user (str): destination username
        pword (str): destination password
        source (str): source file path
        destination (str): destination file path
    """
    msg = 'Transfer to IP: %s , username: %s , password: %s, source path: %s , destination path: %s'%(IP,user,pword,source, destination)
    # print(msg)
    

    if TRANSFER == 0:
        return transfer_data_scp(IP,user,pword,source, destination)

    return transfer_data_scp(IP,user,pword,source, destination) #default


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
            print("Received file as output - %s." % event.src_path) 
            # print(event.src_path, event.event_type)  # print now only for degug
            outputfile = event.src_path.split('/')[-1].split('_')[0]

            # print(outputfile)
            end_times[outputfile] = time.time()
            
            # print("ending time is: ", end_times)
            exec_times[outputfile] = end_times[outputfile] - start_times[outputfile]
            print("execution time is: ", exec_times)

            if BOKEH == 2: #used for combined_app with distribute script
                app_name = outputfile.split('-')[0]
                msg = 'makespan '+ app_name + ' '+ outputfile+ ' '+ str(exec_times[outputfile]) 
                demo_help(BOKEH_SERVER,BOKEH_PORT,app_name,msg)

            if BOKEH == 5:
                print(appname)
                msg = 'makespan '+ appoption + ' '+ appname + ' '+ outputfile+ ' '+ str(exec_times[outputfile]) + '\n'
                demo_help(BOKEH_SERVER,BOKEH_PORT,appoption,msg)

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
        
        You can manually place input files into the ``INPUT`` folder (which is under ``centralized_scheduler_with_task_profiler\``):
        
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

            # print('***************************************************')
            print("Received file as input - %s." % event.src_path)  

            if RUNTIME == 1:   
                ts = time.time() 
                s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,event.src_path,ts)
                runtime_receiver_log.write(s)
                runtime_receiver_log.flush()

            inputfile = event.src_path.split('/')[-1]
            t = time.time()
            start_times[inputfile] = t
            # start_times.append(time.time())
            print("start time is: ", start_times)
            new_file_name = os.path.split(event.src_path)[-1]


            #This part should be optimized to avoid hardcoding IP, user and password
            #of the first task node
            IP = os.environ['CHILD_NODES_IPS']
            source = event.src_path
            destination = os.path.join('/centralized_scheduler', 'input', new_file_name)
            transfer_data(IP,username, password,source, destination)
        
        # bottleneck['receiveinput'].append(txec)
        # print(np.mean(bottleneck['receiveinput']))
        # print('***************************************************')
def main():
    """
        -   Read configurations (DAG info, node info) from ``nodes.txt`` and ``configuration.txt``
        -   Monitor ``INPUT`` folder for the incoming files
        -   Whenever there is a new file showing up in ``INPUT`` folder, copy the file to the ``INPUT`` folder of the first scheduled node.
        -   Collect execution profiling information from the system.
    """

    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    # Prepare transfer-runtime file:
    global runtime_sender_log, RUNTIME,TRANSFER, transfer_type, appname,appoption

    RUNTIME = int(config['CONFIG']['RUNTIME'])
    TRANSFER = int(config['CONFIG']['TRANSFER'])
    appname = os.environ['APPNAME']
    appoption = os.environ['APPOPTION']

    if TRANSFER == 0:
        transfer_type = 'scp'

    runtime_sender_log = open(os.path.join(os.path.dirname(__file__), 'runtime_transfer_sender.txt'), "w")
    s = "{:<10} {:<10} {:<10} {:<10} \n".format('Node_name', 'Transfer_Type', 'File_Path', 'Time_stamp')
    runtime_sender_log.write(s)
    runtime_sender_log.close()
    runtime_sender_log = open(os.path.join(os.path.dirname(__file__), 'runtime_transfer_sender.txt'), "a")
    #Node_name, Transfer_Type, Source_path , Time_stamp

    if RUNTIME == 1:
        global runtime_receiver_log
        runtime_receiver_log = open(os.path.join(os.path.dirname(__file__), 'runtime_transfer_receiver.txt'), "w")
        s = "{:<10} {:<10} {:<10} {:<10} \n".format('Node_name', 'Transfer_Type', 'File_path', 'Time_stamp')
        runtime_receiver_log.write(s)
        runtime_receiver_log.close()
        runtime_receiver_log = open(os.path.join(os.path.dirname(__file__), 'runtime_transfer_receiver.txt'), "a")
        #Node_name, Transfer_Type, Source_path , Time_stamp

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

    # print("TASK1: ", dag_info[0])
    # print("DAG: ", dag_info[1])
    # print("HOSTS: ", dag_info[2])

    global last_tasks
    last_tasks = set()
    for task in dag_info[1]:
        if 'home' in dag_info[1][task]:
            last_tasks.add(task)

    # print("LAST TASKS: ", last_tasks)

    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])


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