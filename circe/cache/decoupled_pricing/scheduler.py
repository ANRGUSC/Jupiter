#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on the scheduler node of CIRCE. 

"""

__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import sys
sys.path.append("../")
import paramiko
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
import urllib
import _thread
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient
import datetime
import json
import paho.mqtt.client as mqtt
import pyinotify






app = Flask(__name__)

# Per task times
start_time = defaultdict(list)
end_time = defaultdict(list)

rt_enter_time = defaultdict(list)
rt_exec_time = defaultdict(list)
rt_finish_time = defaultdict(list)

rt_enter_time_computingnode = defaultdict(list)
rt_exec_time_computingnode = defaultdict(list)
rt_finish_time_computingnode = defaultdict(list)

def demo_help(server,port,topic,msg):
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()


def announce_mapping():

    try:
        tmp_assignments = request.args.get('assignments')
        print("Received mapping announcement from controller")
        tmp = tmp_assignments.split(',')
        for task in tmp:
            global_task_node_map[task.split(':')[0]]=task.split(':')[1]
        print("Sending global task information to all worker nodes")
        announce_mapping_to_workers()
    except Exception as e:
        print("Received mapping announcement from controller failed")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/announce_mapping', 'announce_mapping', announce_mapping)






def announce_mapping_to_workers():
    try:
        print('Announce full mapping to all compute worker node')
        tmp_assignments = ",".join(("{}:{}".format(*i) for i in global_task_node_map.items()))

        t = time.time()
        for compute_host in all_compute_host:
            url = "http://" + compute_host + "/announce_mapping_worker"
            params = {'home_id':my_id,'assignments': tmp_assignments,'mapping_time':t}
            params = urllib.parse.urlencode(params)
            req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
            res = urllib.request.urlopen(req)
            res = res.read()
            res = res.decode('utf-8')
        if BOKEH==3:    
            topic = 'msgoverhead_home'
            msg = 'msgoverhead pricedecoupled computehome announcemapping %d\n'%(len(all_compute_host))
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    except Exception as e:
        print('Announce full mapping to compute home node failed')
        print(e)
        return "not ok"
    return res


def return_output_files():
    """
    Return number of output files
    
    Returns:
        int: number of output files
    """
    num_files = len(os.listdir("output/"))
    print("Received request for number of output files. Current done:", num_files)
    return json.dumps(num_files)
app.add_url_rule('/', 'return_output_files', return_output_files)



def recv_runtime_profile_computingnode():
    """

    Receiving run-time profiling information for every task (task name, start time stats, waiting time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """

    global rt_enter_time_computingnode
    global rt_exec_time_computingnode
    global rt_finish_time_computingnode

    try:
        worker_node = request.args.get('work_node')
        msg = request.args.get('msg').split()
        task_name = request.args.get('task_name')
        
        if msg[0] == 'rt_enter':
            rt_enter_time_computingnode[(worker_node,task_name,msg[1])] = float(msg[2])
        elif msg[0] == 'rt_exec' :
            rt_exec_time_computingnode[(worker_node,task_name,msg[1])] = float(msg[2])
        else: #rt_finish
            rt_finish_time_computingnode[(worker_node,task_name,msg[1])] = float(msg[2])

            print('----------------------------')
            print('Runtime info at each computing node')
            print("Worker node: "+ worker_node)
            print("Input file : "+ msg[1])
            print("Task name: " + task_name)
            print("Total duration time:" + str(rt_finish_time_computingnode[(worker_node,task_name, msg[1])] - rt_enter_time_computingnode[(worker_node,task_name, msg[1])]))
            print("Waiting time:" + str(rt_exec_time_computingnode[(worker_node,task_name,msg[1])] - rt_enter_time_computingnode[(worker_node,task_name,msg[1])]))
            print(worker_node + " execution time:" + str(rt_finish_time_computingnode[(worker_node,task_name,msg[1])] - rt_exec_time_computingnode[(worker_node,task_name,msg[1])]))
            
            print('----------------------------')  
            if task_name in last_tasks:
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
                log_file = open(os.path.join(os.path.dirname(__file__), 'runtime_tasks_computingnode.txt'), "w")
                s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Worker_node','Task_name','input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time')
                print(s)
                log_file.write(s)
                for k, v in rt_enter_time_computingnode.items():
                    worker, task, file = k
                    if k in rt_finish_time_computingnode:
                        elapse = rt_finish_time_computingnode[k]-v
                        duration = rt_finish_time_computingnode[k]-rt_exec_time_computingnode[k]
                        waiting = rt_exec_time_computingnode[k]-v
                        s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(worker, task, file, v, rt_exec_time_computingnode[k],rt_finish_time_computingnode[k],str(elapse),str(duration),str(waiting))
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
app.add_url_rule('/recv_runtime_profile_computingnode', 'recv_runtime_profile_computingnode', recv_runtime_profile_computingnode)

def transfer_data_scp(ID,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        IP (str): destination ID
        user (str): username
        pword (str): password
        source (str): source file path
        destination (str): destination file path
    """

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
            print('File transfer failed, will retry in 2 seconds')
            time.sleep(2)
            retry += 1
    if retry == num_retries:
        s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,source,ts)
        runtime_sender_log.write(s)
        runtime_sender_log.flush()

    

def transfer_data(ID,user,pword,source, destination):
    """Transfer data with given parameters
    
    Args:
        ID (str): destination ID 
        user (str): destination username
        pword (str): destination password
        source (str): source file path
        destination (str): destination file path
    """
    msg = 'Transfer to ID: %s , username: %s , password: %s, source path: %s , destination path: %s'%(ID,user,pword,source, destination)
    

    if TRANSFER == 0:
        return transfer_data_scp(ID,user,pword,source, destination)

    return transfer_data_scp(ID,user,pword,source, destination) #default


class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)


class Handler1(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        print("Received file as output - %s." % event.pathname)
        outputfile = event.pathname.split('/')[-1].split('_')[0]

        end_times[outputfile] = time.time()
        exec_times[outputfile] = end_times[outputfile] - start_times[outputfile]
        print("execution time is: ", exec_times)

        if BOKEH==3:
            msg = 'makespan '+ appoption + ' '+ appname + ' '+ outputfile+ ' '+ str(exec_times[outputfile]) + '\n'
            demo_help(BOKEH_SERVER,BOKEH_PORT,appoption,msg)
           

def announce_input(input_file, input_time):
    """
    Raises:
        Exception: request if successful, ``not ok`` if failed
    """
    try:
        print('Announce input file to all compute worker node')
        for compute_host in all_compute_host:
            url = "http://" + compute_host + "/announce_input_worker"
            params = {'home_id':my_id,'input_file': input_file, 'input_time':input_time}
            params = urllib.parse.urlencode(params)
            req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
            res = urllib.request.urlopen(req)
            res = res.read()
            res = res.decode('utf-8')
        if BOKEH==3:    
            topic = 'msgoverhead_home'
            msg = 'msgoverhead pricedecoupled computehome announceinput %d\n'%(len(all_compute_host))
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    except Exception as e:
        print('Announce input files to compute nodes failed')
        print(e)
        return "not ok"
    return res

class Handler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        print("Received file as input - %s." % event.pathname)
        if RUNTIME == 1:   
            ts = time.time() 
            s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,event.pathname,ts)
            runtime_receiver_log.write(s)
            runtime_receiver_log.flush()

        inputfile = event.pathname.split('/')[-1]
        t = time.time()
        start_times[inputfile] = t
        input_file = inputfile.split('.')[0]
        announce_input(input_file, t)
        new_file_name = os.path.split(event.pathname)[-1]
        while first_task not in global_task_node_map:
            print('Not yet update global task mapping information')
            time.sleep(2)

        print('Send file to the first node')
        print(global_task_node_map[first_task])
    
        source = event.pathname
        destination = os.path.join('/centralized_scheduler', 'input', first_task,my_task,new_file_name)
        transfer_data(global_task_node_map[first_task],username, password,source, destination)
        
def get_taskmap():
    """Get the task map from ``config.json`` and ``dag.txt`` files.
    
    Returns:
        - dict: tasks - DAG dictionary
        - list: task_order - (DAG) task list in the order of execution
        - list: super_tasks 
        - list: non_tasks - tasks not belong to DAG
    """
    configs = json.load(open('centralized_scheduler/config.json'))
    task_map = configs['taskname_map']
    execution_map = configs['exec_profiler']
    tasks_info = open('centralized_scheduler/dag.txt', "r")

    task_order = []#create the  (DAG) task list in the order of execution
    super_tasks = []
    tasks = {} #create DAG dictionary
    count = 0
    non_tasks = []
    for line in tasks_info:
        if count == 0:
            count += 1
            continue

        data = line.strip().split(" ")
        if task_map[data[0]][1] == True and execution_map[data[0]] == False:
            if data[0] not in super_tasks:
                super_tasks.append(data[0])

        if task_map[data[0]][1] == False and execution_map[data[0]] == False:
            if data[0] not in non_tasks:
                non_tasks.append(data[0])

        if task_map[data[0]][1] == False:
            continue

        tasks.setdefault(data[0], [])
        if data[0] not in task_order:
            task_order.append(data[0])
        for i in range(3, len(data)):
            if  data[i] != 'home' and task_map[data[i]][1] == True :
                tasks[data[0]].extend([data[i]])
    return tasks, task_order, super_tasks, non_tasks

def start_evaluate():
    print('Start the evaluation process')
    os.system('python3 evaluate.py &')

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
    global runtime_sender_log, RUNTIME,TRANSFER, transfer_type
    RUNTIME = int(config['CONFIG']['RUNTIME'])
    TRANSFER = int(config['CONFIG']['TRANSFER'])

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

    
    global tasks, task_order, super_tasks, non_tasks
    tasks, task_order, super_tasks, non_tasks = get_taskmap()
    print('----------- TASKS INFO')
    print(tasks)
    print(task_order)
    print(super_tasks)
    print(non_tasks)



    global FLASK_DOCKER, FLASK_SVC, MONGO_SVC, username, password, ssh_port, num_retries, first_task, appname, appoption

    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    FLASK_SVC      = int(config['PORT']['FLASK_SVC'])
    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    first_task  = os.environ['CHILD_NODES']
    appname = os.environ['APPNAME']
    appoption = os.environ['APPOPTION']

    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

    global manager
    manager = Manager()

    global global_task_node_map
    global_task_node_map = manager.dict()

    global start_times
    global end_times
    global exec_times

    # End-to-end metrics
    start_times = manager.dict()
    end_times = manager.dict()
    exec_times = manager.dict()
    
    

    global all_computing_nodes,all_computing_ips, node_ip_map,my_id,my_task, first_flag, all_compute_host,num_computing_nodes

    all_computing_nodes = os.environ["ALL_COMPUTING_NODES"].split(":")
    all_computing_ips = os.environ["ALL_COMPUTING_IPS"].split(":")
    num_computing_nodes = len(all_computing_nodes)
    node_ip_map = dict(zip(all_computing_nodes, all_computing_ips))
    all_compute_host = [x+':'+str(FLASK_SVC) for x in all_computing_ips]

    my_id = os.environ['TASK']
    my_task = my_id.split('-')[1]

    global home_nodes,home_ids,home_ips,home_ip_map

    home_nodes = os.environ['HOME_NODE'].split(' ')
    home_ids = [x.split(':')[0] for x in home_nodes]
    home_ips = [x.split(':')[1] for x in home_nodes]
    home_ip_map = dict(zip(home_ids, home_ips))

    global combined_ip_map,combined_ips,combined_nodes

    combined_nodes = home_ids + all_computing_nodes
    combined_ips = home_ips + all_computing_ips
    combined_ip_map = dict(zip(combined_nodes,combined_ips))
    

    path1 = 'configuration.txt'
    path2 = 'nodes.txt'
    dag_info = read_config(path1,path2)

    #get DAG and home machine info
    dag = dag_info[1]
    hosts=dag_info[2]
    first_flag = dag_info[1][first_task][1]

    print("TASK: ", dag_info[0])
    print("DAG: ", dag_info[1])
    print("HOSTS: ", dag_info[2])
    

    global last_tasks
    last_tasks = set()
    for task in dag_info[1]:
        if 'home' in dag_info[1][task]:
            last_tasks.add(task)


    web_server = MonitorRecv()
    web_server.start()

    _thread.start_new_thread(start_evaluate,())

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
    eh1 = Handler1()
    notifier1= pyinotify.Notifier(wm1, eh1)
    notifier1.loop()


    



    
    
if __name__ == '__main__':

    main()