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
from multiprocessing import Process, Manager
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
import random
import pyinotify


app = Flask(__name__)

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

def recv_datasource():
    """

    Receiving run-time profiling information from WAVE/HEFT for every task (task name, start time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """
    global start_times, end_times
    try:
        # print('Receive final runtime profiling')
        filename = request.args.get('filename')
        filetype = request.args.get('filetype')
        ts = request.args.get('time')

        print("Received flask message:", filename, filetype,ts)
        if filetype == 'input':
            start_times[filename]=float(ts)
        else:
            end_times[filename]=float(ts)
        
    except Exception as e:
        print("Bad reception or failed processing in Flask")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_monitor_datasource', 'recv_datasource', recv_datasource)

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

        print("Received flask message:", worker_node, msg, ts)
        if msg == 'start':
            start_time[worker_node].append(ts)
        else:
            end_time[worker_node].append(ts)
            if worker_node in last_tasks:
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
        
        if msg[0] == 'rt_enter':
            rt_enter_time[(worker_node,msg[1])] = float(msg[2])
        elif msg[0] == 'rt_exec' :
            rt_exec_time[(worker_node,msg[1])] = float(msg[2])
        else: #rt_finish
            rt_finish_time[(worker_node,msg[1])] = float(msg[2])
            if worker_node in last_tasks:
                # Per task stats:
                print('********************************************') 
                print("Received final output at home: Runtime profiling info:")
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
                log_file.write(s)
                for k, v in rt_enter_time.items():
                    worker, file = k
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
    #the child nodes
    retry = 0
    ts = -1
    while retry < num_retries:
        try:
            nodeIP = combined_ip_map[ID]
            print(nodeIP)
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, nodeIP, destination)
            print(cmd)
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
    if retry == num_retries:
        s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,source,ts)
        runtime_sender_log.write(s)
        runtime_sender_log.flush()

    

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
    # print(msg)
    

    if TRANSFER == 0:
        return transfer_data_scp(ID,user,pword,source, destination)

    return transfer_data_scp(ID,user,pword,source, destination) #default


class MyHandler(pyinotify.ProcessEvent):
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

        print("Received file as output - %s." % event.pathname)  

        if RUNTIME == 1:   
            ts = time.time() 
            s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,event.pathname,ts)
            runtime_receiver_log.write(s)
            runtime_receiver_log.flush()

        global start_times, end_times
        global exec_times
        global count

        print("Received file as output - %s." % event.pathname) 
        # print(event.src_path, event.event_type)  # print now only for degug
        outputfile = event.pathname.split('/')[-1].split('_')[0]

        # print(outputfile)
        end_times[outputfile] = time.time()
        
        exec_times[outputfile] = end_times[outputfile] - start_times[outputfile]
        print("start time is: ", start_times)
        print("end time is: ", end_times)
        print("execution time is: ", exec_times)

        if BOKEH == 2: #used for combined_app with distribute script
            app_name = outputfile.split('-')[0]
            msg = 'makespan '+ app_name + ' '+ outputfile+ ' '+ str(exec_times[outputfile]) 
            demo_help(BOKEH_SERVER,BOKEH_PORT,app_name,msg)

        if BOKEH == 3:
            msg = 'makespan '+ appoption + ' '+ appname + ' '+ outputfile+ ' '+ str(exec_times[outputfile]) + '\n'
            demo_help(BOKEH_SERVER,BOKEH_PORT,appoption,msg)


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
        global start_times, end_times

        print("Received file as input - %s." % event.pathname)  

        if RUNTIME == 1:   
            ts = time.time() 
            s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,event.pathname,ts)
            runtime_receiver_log.write(s)
            runtime_receiver_log.flush()

        inputfile = event.pathname.split('/')[-1]
        t = time.time()
        start_times[inputfile] = t
        new_file_name = os.path.split(event.pathname)[-1]

        # This part should be optimized to avoid hardcoding IP, user and password
        # of the first task node
        # IP = os.environ['CHILD_NODES_IPS']
        # With split, example ENVs on CIRCE home node
        # CHILD_NODES=task0-1/0.158:task0-2/0.363:task0-3/0.479
        # CHILD_NODES_IPS=10.102.129.178/0.158:10.99.13.47/0.363:10.106.166.88/0.479
        # for now only support one child node on home node
        child_nodes = os.environ['CHILD_NODES']
        source = event.pathname
        print("child_nodes")
        print(child_nodes)
        ID = self.random_select(child_nodes)
        destination = os.path.join('/centralized_scheduler', 'input', new_file_name)
        print(ID, destination)
        transfer_data(ID,username, password,source, destination)
              
    def random_select(self, child_nodes):
        
        # CHILD_NODES=task0-1/0.158:task0-2/0.363:task0-3/0.479
        tmp = child_nodes.split(':')
        tasks = []
        probs = []
        for var in tmp:
            tasks.append(var.split('/')[0])
            probs.append(1 if len(var.split('/')) == 1 else var.split('/')[1])
        if len(probs) == 1:
            return tasks[0]
        chosen_task = ""
        rand = random.randint(1, 1000)
        probs = [1000*float(v) for v in probs]
        for k in range(len(probs)-1):
            probs[k+1] = probs[k] + probs[k+1]
        probs[len(probs)-1] = 1000
        if rand <= probs[0]:
            chosen_task = tasks[0]
        else:
            for k in range(len(probs)-1):
                if rand > probs[k] and rand <= probs[k+1]:
                    chosen_task = tasks[k+1]
        return chosen_task
        
            
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

    global combined_ip_map
    combined_ip_map = dict()
    #{'task0-1/0.159:task0-2/0.364:task0-3/0.477': '10.107.147.223/0.159:10.96.120.197/0.364:10.100.198.217/0.477'
    child_names = os.environ['CHILD_NODES'].split(':')
    child_names = [name.split('/')[0] for name in child_names]
    child_ips = os.environ['CHILD_NODES_IPS'].split(':')
    child_ips = [ip.split('/')[0] for ip in child_ips]
    for i in range(len(child_names)):
        combined_ip_map[child_names[i]] = child_ips[i] 

    path1 = 'configuration.txt'
    path2 = 'nodes.txt'
    dag_info = read_config(path1,path2)
    """
    example output:
    [
        'task0', 
         {
             'task0': ['1', 'true', 'task1', 'task2'], 
             'task1': ['1', 'true', 'task3'], 
             'task3': ['2', 'true', 'home'], 
             'task2': ['1', 'true', 'task3']
         }, 
         {
             'home': ['home', 'ubuntu-s-2vcpu-4gb-sfo2-01']
         }
    ]
    """
    
    global manager
    manager = Manager()

    global start_times, end_times, exec_times
    start_times = manager.dict()
    end_times = manager.dict()
    exec_times = manager.dict()
    
    global count, start_time,end_time, rt_enter_time, rt_exec_time, rt_finish_time
    count = 0
    start_time = defaultdict(list)
    end_time = defaultdict(list)

    rt_enter_time = defaultdict(list)
    rt_exec_time = defaultdict(list)
    rt_finish_time = defaultdict(list)

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

    web_server = MonitorRecv()
    web_server.start()

    # watch manager
    wm = pyinotify.WatchManager()
    input_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'input/')
    wm.add_watch(input_folder, pyinotify.ALL_EVENTS, rec=True)
    print('starting the input monitoring process\n')
    eh = Handler()
    notifier = pyinotify.ThreadedNotifier(wm, eh)
    notifier.start()

    output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'output/')
    wm1 = pyinotify.WatchManager()
    wm1.add_watch(output_folder, pyinotify.ALL_EVENTS, rec=True)
    print('starting the output monitoring process\n')
    eh1 = MyHandler()
    notifier1= pyinotify.Notifier(wm1, eh1)
    notifier1.loop()
    
    
if __name__ == '__main__':

    main()
