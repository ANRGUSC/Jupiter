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
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, nodeIP, destination)
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


        #This part should be optimized to avoid hardcoding IP, user and password
        #of the first task node
        # IP = os.environ['CHILD_NODES_IPS']
        ID = os.environ['CHILD_NODES']
        source = event.pathname
        destination = os.path.join('/centralized_scheduler', 'input', new_file_name)
        transfer_data(ID,username, password,source, destination)

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
    combined_ip_map[os.environ['CHILD_NODES']]= os.environ['CHILD_NODES_IPS']

    path1 = 'configuration.txt'
    path2 = 'nodes.txt'
    dag_info = read_config(path1,path2)

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

    """
    DAG info: something like this
    [
    'task0', 
     {
          'task0': ['1', 'false', 'task1', 'task3', 'task2', 'task4'], 
          'task1': ['1', 'false', 'task4'], 
          'task2': ['1', 'false', 'task5', 'task4', 'task6'], 
          'task3': ['1', 'false', 'task5', 'task4', 'task6'], 
          'task4': ['4', 'false', 'task6'], 
          'task5': ['2', 'false', 'task6'], 
          'task6': ['4', 'false', 'home']
     }, 
     {
         'home': ['home', 'ubuntu-s-2vcpu-4gb-sfo2-01']
     }
    ]
    """
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
    """
    filesystem change monitoring tool, something like this:
    zxc@zxc-ThinkPad-T470-W10DG:~$ python3 -m pyinotify -v ~
    [2020-03-14 14:56:35,773 pyinotify DEBUG] Start monitoring ['/home/zxc'], (press c^c to halt pyinotify)
    [2020-03-14 14:56:35,773 pyinotify DEBUG] New <Watch wd=1 path=/home/zxc mask=4095 proc_fun=None auto_add=None exclude_filter=<function  
    WatchManager.<lambda> at 0x7f022d455158> dir=True >
    [2020-03-14 14:58:57,420 pyinotify DEBUG] Event queue size: 32
    [2020-03-14 14:58:57,422 pyinotify DEBUG] <_RawEvent cookie=0 mask=0x20 name=sshjupiter.sh wd=1 >
    <Event dir=False mask=0x20 maskname=IN_OPEN name=sshjupiter.sh path=/home/zxc pathname=/home/zxc/sshjupiter.sh wd=1 >
    [2020-03-14 14:58:57,423 pyinotify DEBUG] Event queue size: 272
    [2020-03-14 14:58:57,424 pyinotify DEBUG] <_RawEvent cookie=0 mask=0x100 name=sshjupiter (copy).sh wd=1 >
    [2020-03-14 14:58:57,425 pyinotify DEBUG] <_RawEvent cookie=0 mask=0x20 name=sshjupiter (copy).sh wd=1 >
    [2020-03-14 14:58:57,425 pyinotify DEBUG] <_RawEvent cookie=0 mask=0x2 name=sshjupiter (copy).sh wd=1 >
    [2020-03-14 14:58:57,426 pyinotify DEBUG] <_RawEvent cookie=0 mask=0x10 name=sshjupiter.sh wd=1 >
    [2020-03-14 14:58:57,426 pyinotify DEBUG] <_RawEvent cookie=0 mask=0x8 name=sshjupiter (copy).sh wd=1 >
    [2020-03-14 14:58:57,426 pyinotify DEBUG] <_RawEvent cookie=0 mask=0x4 name=sshjupiter (copy).sh wd=1 >
    <Event dir=False mask=0x100 maskname=IN_CREATE name=sshjupiter (copy).sh path=/home/zxc pathname=/home/zxc/sshjupiter (copy).sh wd=1 >
    <Event dir=False mask=0x20 maskname=IN_OPEN name=sshjupiter (copy).sh path=/home/zxc pathname=/home/zxc/sshjupiter (copy).sh wd=1 >
    <Event dir=False mask=0x2 maskname=IN_MODIFY name=sshjupiter (copy).sh path=/home/zxc pathname=/home/zxc/sshjupiter (copy).sh wd=1 >
    <Event dir=False mask=0x10 maskname=IN_CLOSE_NOWRITE name=sshjupiter.sh path=/home/zxc pathname=/home/zxc/sshjupiter.sh wd=1 >
    <Event dir=False mask=0x8 maskname=IN_CLOSE_WRITE name=sshjupiter (copy).sh path=/home/zxc pathname=/home/zxc/sshjupiter (copy).sh wd=1 >
    <Event dir=False mask=0x4 maskname=IN_ATTRIB name=sshjupiter (copy).sh path=/home/zxc pathname=/home/zxc/sshjupiter (copy).sh wd=1 >
    [2020-03-14 14:59:15,852 pyinotify DEBUG] Event queue size: 48
    [2020-03-14 14:59:15,852 pyinotify DEBUG] <_RawEvent cookie=38622 mask=0x40 name=sshjupiter (copy).sh wd=1 >
    <Event cookie=38622 dir=False mask=0x40 maskname=IN_MOVED_FROM name=sshjupiter (copy).sh path=/home/zxc pathname=/home/zxc/sshjupiter (copy).sh wd=1 >

    """
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
