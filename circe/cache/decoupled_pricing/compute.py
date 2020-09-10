#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on every computing node of the system.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

import sys
sys.path.append("../")
import configparser
import jupiter_config
import os
import json
from multiprocessing import Process, Manager
import multiprocessing
from flask import Flask, request
from os import path
import json
import _thread
import threading
import csv
from pymongo import MongoClient
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import urllib
from apscheduler.schedulers.background import BackgroundScheduler
from readconfig import read_config
from shutil import copyfile
import datetime
from collections import defaultdict 
import pyinotify

app = Flask(__name__)

def k8s_read_dag(dag_info_file):
  """read the dag from the file input
  
  Args:
      dag_info_file (str): path of DAG file
  
  Returns:
      dict: DAG information 
  """
  dag_info=[]
  config_file = open(dag_info_file,'r')
  dag_size = int(config_file.readline())

  dag={}
  for i, line in enumerate(config_file, 1):
      dag_line = line.strip().split(" ")
      if i == 1:
          dag_info.append(dag_line[0])
      dag.setdefault(dag_line[0], [])
      for j in range(1,len(dag_line)):
          dag[dag_line[0]].append(dag_line[j])
      if i == dag_size:
          break

  dag_info.append(dag)
  return dag_info


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
    print("tasks: ", tasks)
    print("task order", task_order) #task_list
    print("super tasks", super_tasks)
    print("non tasks", non_tasks)
    return tasks, task_order, super_tasks, non_tasks


def prepare_global_info():


    """Get information of corresponding profiler (network profiler, execution profiler)"""
    global self_profiler_ip,profiler_ip, profiler_nodes,exec_home_ip, self_name,self_ip, task_controllers, task_controllers_ips, home_ips,home_ids, home_ip_map, node_ip_map, computing_ips
    profiler_ip = os.environ['ALL_PROFILERS'].split(' ')
    profiler_ip = [info.split(":") for info in profiler_ip]
    profiler_ip = profiler_ip[0][1:]

    profiler_nodes = os.environ['ALL_PROFILERS_NODES'].split(' ')
    profiler_nodes = [info.split(":") for info in profiler_nodes]
    profiler_nodes = profiler_nodes[0][1:]
   
    self_profiler_ip = os.environ['PROFILERS']
    exec_home_ip = os.environ['EXECUTION_HOME_IP']
    self_name = os.environ['NODE_NAME']
    self_ip = os.environ['SELF_IP']
    home_nodes = os.environ['HOME_NODE'].split(' ')
    home_ids = [x.split(':')[0] for x in home_nodes]
    home_ips = [x.split(':')[1] for x in home_nodes]
    home_ip_map = dict(zip(home_ids, home_ips))
    

    global computing_nodes,computing_ips 
    computing_nodes = os.environ['ALL_COMPUTING_NODES'].split(':')
    computing_ips = os.environ['ALL_COMPUTING_IPS'].split(':')
    node_ip_map = dict(zip(computing_nodes, computing_ips))

    global combined_ip_map,combined_ips,combined_nodes

    combined_nodes = home_ids + computing_nodes
    combined_ips = home_ips + computing_ips
    combined_ip_map = dict(zip(combined_nodes,combined_ips))

    global manager,task_mul, count_mul, queue_mul, next_mul, files_mul, controllers_id_map, pass_time
    

    manager = Manager()
    task_mul = manager.dict() # list of incoming tasks and files
    count_mul = manager.dict() # number of input files required for each task
    queue_mul = manager.dict() # tasks which have not yet been processed
    next_mul = manager.dict() # information of next node (IP,username,pass) fo the current file
    files_mul = manager.dict()
    controllers_id_map = manager.dict()
    pass_time = manager.dict()

    global global_task_node_map
    global_task_node_map = manager.dict()


    global start_times, mapping_times, mapping_input_id
    start_times = manager.dict()
    mapping_times = manager.list()
    mapping_input_id = manager.dict()


    global home_node_host_ports, dag
    home_node_host_ports = dict()
    for home_id in home_ids:
        home_node_host_ports[home_id] = home_ip_map[home_id] + ":" + str(FLASK_SVC)

    dag_file = '/centralized_scheduler/dag.txt'
    dag_info = k8s_read_dag(dag_file)
    dag = dag_info[1]


    global tasks, task_order, super_tasks, non_tasks
    tasks, task_order, super_tasks, non_tasks = get_taskmap()

    global ip_profilers_map,profilers_ip_map, controllers_ip_map, computing_ip_map, profilers_ip_homes
    
    ip_profilers_map = dict(zip(profiler_ip, profiler_nodes))
    profilers_ip_map = dict(zip(profiler_nodes, profiler_ip))

    profilers_ip_homes = [profilers_ip_map[x] for x in home_ids]
    computing_ip_map = dict(zip(computing_nodes, computing_ips))

    global next_tasks_map,last_tasks_map
    next_tasks_map = dict()
    last_tasks_map = dict()

    
    for task in dag:
        next_tasks_map[task] = dag[task][2:]
        for last_task in dag[task][2:]:
            if last_task not in last_tasks_map:
                last_tasks_map[last_task] = [task]
            else:    
                last_tasks_map[last_task].append(task)

    

    last_tasks_map[os.environ['CHILD_NODES']] = []
    for home_id in home_ids:
        last_tasks_map[home_id] = last_tasks_map['home'] 
        # global_task_node_map[home_id]  = home_id
        next_tasks_map[home_id] = [os.environ['CHILD_NODES']]
        last_tasks_map[os.environ['CHILD_NODES']].append(home_id)

    global name_convert_out, name_convert_in
    name_convert_in = dict()
    name_convert_out = dict()
    convert_name_file = '/centralized_scheduler/name_convert.txt'
    with open(convert_name_file) as f:
        lines = f.readlines()
        for line in lines:
            info = line.rstrip().split(' ')
            name_convert_out[info[0]] = info[1]
            name_convert_in[info[0]] = info[2]    

    # CHECK NON_DAG tasks
    global configs, taskmap

    configs = json.load(open('/centralized_scheduler/config.json'))
    taskmap = configs["taskname_map"]
    execution_map = configs['exec_profiler']


    print('Generating task folders for OUTPUT\n')
    global task_module
    task_module = {}
    for task in dag:
        if taskmap[task][1] and execution_map[task]: #DAG
            task_module[task] = __import__(task)
            cmd = "mkdir centralized_scheduler/output/"+task 
            os.system(cmd)
            for home_id in home_ids:
                cmd = "mkdir centralized_scheduler/output/"+task+"/" + home_id
                os.system(cmd)

    print('Generating task folders for INPUT\n')
    for task in dag:
        if taskmap[task][1]: #DAG
            cmd = "mkdir centralized_scheduler/input/"+task 
            os.system(cmd)
            for home_id in home_ids:
                cmd = "mkdir centralized_scheduler/input/"+task+"/" + home_id
                os.system(cmd)

  
  
def announce_input_worker():
    try:
        print('Receive input announcement from the home node')
        tmp_file = request.args.get('input_file')
        tmp_time = request.args.get('input_time')
        tmp_info = request.args.get('home_id')
        tmp_home = tmp_info.split('-')[1]
        print("Received input announcement from home compute")
        start_times[(tmp_home,tmp_file)] = tmp_time
        print(global_task_node_map)
        print(mapping_times)
        if len(mapping_times)==0: 
            mapping_input_id[(tmp_home,tmp_file)] = 0
        else:
            mapping_input_id[(tmp_home,tmp_file)] = len(mapping_times)-1 #ID of last mapping
        print(mapping_input_id)

    except Exception as e:
        print("Received mapping announcement from controller failed")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/announce_input_worker', 'announce_input_worker', announce_input_worker)

def announce_mapping_worker():
    try:
        tmp_assignments = request.args.get('assignments')
        tmp_info = request.args.get('home_id')
        tmp_home = tmp_info.split('-')[1]
        tmp_time = request.args.get('mapping_time')
        print("Received mapping announcement from home compute")
        tmp = tmp_assignments.split(',')

        mapping_times.append(tmp_time)

        for task in tmp:
            global_task_node_map[len(mapping_times)-1,tmp_home,task.split(':')[0]]=task.split(':')[1]

        

    except Exception as e:
        print("Received mapping announcement from controller failed")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/announce_mapping_worker', 'announce_mapping_worker', announce_mapping_worker)

def execute_task(home_id,task_name,file_name, filenames, input_path, output_path):
    """Execute the task given the input information
    
    Args:
        task_name (str): incoming task name
        filenames (str): incoming files
        input_path (str): input file path
        output_path (str): output file path
    """
    ts = time.time()
    runtime_info = 'rt_exec '+ file_name+ ' '+str(ts)
    send_runtime_profile_computingnode(runtime_info,task_name,home_id)
    dag_task = multiprocessing.Process(target=task_module[task_name].task, args=(filenames, input_path, output_path))
    dag_task.start()
    dag_task.join()
    
    
def transfer_mapping_decorator(TRANSFER=0):
    """Mapping the chosen TA2 module (network and resource monitor) based on ``jupiter_config.PROFILER`` in ``jupiter_config.ini``
    
    Args:
        TRANSFER (int, optional): TRANSFER specified from ``jupiter_config.ini``, default method is SCP
    
    Returns:
        function: chosen transfer method
    """
    
    def transfer_data_scp(ID,user,pword,source, destination):
        """Transfer data using SCP
        
        Args:
            IP (str): destination ID
            user (str): destination username
            pword (str): destination password
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
                ts = time.time()
                s = "{:<10} {:<10} {:<10} {:<10} \n".format(self_name, transfer_type,source,ts)
                runtime_sender_log.write(s)
                runtime_sender_log.flush()
                break
            except:
                print('profiler_worker.txt: SSH Connection refused or File transfer failed, will retry in 2 seconds')
                time.sleep(1)
                retry += 1
        if retry == num_retries:
            s = "{:<10} {:<10} {:<10} {:<10} \n".format(self_name,transfer_type,source,ts)
            runtime_sender_log.write(s)
            runtime_sender_log.flush()

    if TRANSFER==0:
        return transfer_data_scp
    return transfer_data_scp

@transfer_mapping_decorator
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
    print(msg)

def send_runtime_profile_computingnode(msg,task_name,home_id):
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
        # print("Sending message", msg)
        url = "http://" + home_node_host_ports[home_id] + "/recv_runtime_profile_computingnode"
        params = {'msg': msg, "work_node": self_name, "task_name": task_name}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending runtime profiling info to flask server on home FAILED!!!")
        print(e)
        return "not ok"
    return res

def retrieve_input_enter(task_name, file_name):
    """Retrieve the corresponding input name based on the name conversion provided by the user and the output file name in ``name_convert.txt``
    
    Args:
        task_name (str): task name
        file_name (str): name of the file enter at the INPUT folder
    """
    suffix = name_convert_in[task_name]
    prefix = file_name.split(suffix)
    input_name = prefix[0]+name_convert_in['input']
    return input_name

def retrieve_input_finish(task_name, file_name):
    """Retrieve the corresponding input name based on the name conversion provided by the user and the output file name 
    
    Args:
        task_name (str): task name
        file_name (str): name of the file output at the OUTPUT folder
    """
    suffix = name_convert_out[task_name]
    prefix = file_name.split(suffix)
    input_name = prefix[0]+name_convert_in['input']
    return input_name



class Handler1(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        print("Received file as output - %s." % event.pathname)


        new_file = os.path.split(event.pathname)[-1]

        if '_' in new_file:
            temp_name = new_file.split('_')[0]
        else:
            temp_name = new_file.split('.')[0]

        
        ts = time.time()
        
        if RUNTIME == 1:
            s = "{:<10} {:<10} {:<10} {:<10} \n".format(self_name,transfer_type,event.pathname,ts)
            runtime_receiver_log.write(s)
            runtime_receiver_log.flush()

        task_name = event.pathname.split('/')[-3]
        home_id = event.pathname.split('/')[-2]
        input_name = retrieve_input_finish(task_name, temp_name)

        key = (home_id,task_name,input_name)
        flag = next_mul[key][0]
        if next_tasks_map[task_name][0] in home_ids: 
            print('----- next step is home')
            #send runtime info
            
            runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
            send_runtime_profile_computingnode(runtime_info,task_name,home_id)
            transfer_data(home_id,username,password,event.pathname, "/output/"+new_file)   
        else:
            print('----- next step is not home')
            while len(global_task_node_map)==0:
                print('Global task mapping is not loaded')
                time.sleep(1)
            print('Current mapping input list')
            next_hosts = [global_task_node_map[mapping_input_id[(home_id,input_name)],home_id,x] for x in next_tasks_map[task_name]]
            
            print('Sending the output files to the corresponding destinations')
            print(next_hosts)
            if flag=='true': 
                print('not wait, send')
                runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
                send_runtime_profile_computingnode(runtime_info,task_name,home_id)

                #send a single output of the task to all its children 
                destinations = ["/centralized_scheduler/input/" +x + "/"+home_id+"/"+new_file for x in next_tasks_map[task_name]]
                for idx,host in enumerate(next_hosts):
                    if self_ip!=combined_ip_map[host]: # different node
                        print('different node')
                        transfer_data(host,username,password,event.pathname, destinations[idx])
                    else: # same node
                        print('same node')
                        copyfile(event.pathname, destinations[idx])
            else:
                #it will wait the output files and start putting them into queue, send frst output to first listed child, ....
                print('wait')
                if key not in files_mul:
                    files_mul[key] = [event.pathname]
                else:
                    files_mul[key] = files_mul[key] + [event.pathname]
                if len(files_mul[key]) == len(next_hosts):
                    # send runtime info on finishing the task 
                    runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
                    send_runtime_profile_computingnode(runtime_info,task_name,home_id)

                    for idx,host in enumerate(next_hosts):
                        current_file = files_mul[key][idx].split('/')[-1]
                        destinations = "/centralized_scheduler/input/" +next_tasks_map[task_name][idx]+"/"+home_id+"/"+current_file
                        if self_ip!=combined_ip_map[host]:
                            transfer_data(host,username,password,files_mul[key][idx], destinations)
                        else: 
                            copyfile(files_mul[key][idx],destinations)


class Handler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        print("Received file as input - %s." % event.pathname)


        new_file = os.path.split(event.pathname)[-1]
        if '_' in new_file:
            file_name = new_file.split('_')[0]
        else:
            file_name = new_file.split('.')[0]
        ts = time.time()
        home_id = event.pathname.split('/')[-2]
        task_name = event.pathname.split('/')[-3]
        
        input_name = retrieve_input_enter(task_name, file_name)
        runtime_info = 'rt_enter '+ input_name + ' '+str(ts)
        key = (home_id,task_name,input_name)
        send_runtime_profile_computingnode(runtime_info,task_name,home_id)

        flag = dag[task_name][0] 
        task_flag = dag[task_name][1] 
        if key not in task_mul:
            task_mul[key] = [new_file]
            count_mul[key]= int(flag)-1
            next_mul[key] = [task_flag]
        else:
            task_mul[key] = task_mul[key] + [new_file]
            count_mul[key]=count_mul[key]-1

        if count_mul[key] == 0: # enough input files
            incoming_file = task_mul[key]
            if len(incoming_file)==1: 
                filenames = incoming_file[0]
            else:
                filenames = incoming_file

            queue_mul[key] = False 
            
            input_path = os.path.split(event.pathname)[0]
            output_path = input_path.replace("input","output")

            execute_task(home_id,task_name,input_name, filenames, input_path, output_path)
            queue_mul[key] = True
            

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)

def main():
    

    global dag_info
    path1 = 'centralized_scheduler/dag.txt'
    path2 = 'centralized_scheduler/nodes.txt'
    dag_info = read_config(path1,path2)
    # print("DAG: ", dag_info[1])

    global username, password, ssh_port,num_retries, MONGO_DOCKER, MONGO_SVC, FLASK_SVC, FLASK_DOCKER,task_queue_size
    # Load all the confuguration
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    task_queue_size = int(config['OTHER']['TASK_QUEUE_SIZE'])
    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])
    FLASK_SVC    = int(config['PORT']['FLASK_SVC'])
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])

    global first_task
    first_task  = 'task0' #fix later

    update_interval = 1
    
    prepare_global_info()

    # Prepare transfer-runtime file:
    global runtime_sender_log, RUNTIME, TRANSFER, transfer_type
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

    


    web_server = MonitorRecv()
    web_server.start()

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