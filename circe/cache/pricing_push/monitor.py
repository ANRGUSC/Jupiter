#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on every node of the system.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

import multiprocessing
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import sys
import time
import json
import paramiko
import datetime
from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
import netifaces as ni
import platform
from os import path
from socket import gethostbyname, gaierror, error
import multiprocessing
import time
import urllib
import configparser
from multiprocessing import Process, Manager
from flask import Flask, request
import _thread
import threading
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
import paho.mqtt.client as mqtt



app = Flask(__name__)

def demo_help(server,port,topic,msg):
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()

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

def convert_bytes(num):
    """Convert bytes to Kbit as required by HEFT
    
    Args:
        num (int): The number of bytes
    
    Returns:
        float: file size in Kbits
    """
    return num*0.008

def file_size(file_path):
    """Return the file size in bytes
    
    Args:
        file_path (str): The file path
    
    Returns:
        float: file size in bytes
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)

def receive_price_info():
    """
        Receive price from every computing node, choose the most suitable computing node 
    """
    try:
        pricing_info = request.args.get('pricing_info').split('#')
        print("Received pricing info")
        #Network, CPU, Memory, Queue
        node_name = pricing_info[0]

        task_price_cpu[node_name] = float(pricing_info[1])
        task_price_mem[node_name] = float(pricing_info[2])
        task_price_queue[node_name] = float(pricing_info[3].split('$')[0])
        price_net_info = pricing_info[3].split('$')[1:]
        for price in price_net_info:
            task_price_net[node_name,price.split('%')[0]] = float(price.split('%')[1])
        pass_time[node_name] = TimedValue()


    except Exception as e:
        print("Bad reception or failed processing in Flask for pricing announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_price_info', 'receive_price_info', receive_price_info) 


def default_best_node():
    """select the current best node
    """
    print('Select the current best node')
    starttime = time.time()
    w_net = 1 # Network profiling: longer time, higher price
    w_cpu = 1 # Resource profiling : larger cpu resource, lower price
    w_mem = 1 # Resource profiling : larger mem resource, lower price
    w_queue = 1 # Queue : currently 0
    best_node = -1
    task_price_network= dict()
    temp_parents = [x for x in last_tasks_map[self_task] if x not in super_tasks]
    
    if temp_parents[0] not in task_node_map:
        print('Parent tasks not available yet!!!!')
    else:
        source_node = task_node_map[temp_parents[0]]
        print('Current best compute node of parent tasks')
        for (source, dest), price in task_price_net.items():
            if source == source_node:
                task_price_network[dest]= price
        
        task_price_network[source_node] = 0 #the same node
        if len(task_price_network.keys())>1: #net(node,home) not exist
            task_price_summary = dict()
            for item, p in task_price_cpu.items():
                if item in home_ids: continue
                test = pass_time[item].__call__()
                if test==True: 
                    task_price_network[item] = float('Inf')
                task_price_summary[item] = task_price_cpu[item]*w_cpu +  task_price_mem[item]*w_mem + task_price_queue[item]*w_queue + task_price_network[item]*w_net
            
            if task_price_summary:
                best_node = min(task_price_summary,key=task_price_summary.get)
                task_node_map[self_task] = best_node
                mappinglatency = time.time() - starttime   
                if BOKEH==3:    
                    topic = 'mappinglatency_%s'%(app_option)
                    msg = 'mappinglatency pricepush controller%s %s %f\n'%(self_task,app_name,mappinglatency)
                    demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
        else:
            print('Task price summary is not ready yet.....') 
        
    
    



def update_best_node():
    """Select the best node from price information of all nodes, either default or customized from user price file
    """
    try:
        print('Update best assignment node to all computing nodes and home nodes')
        for computing_ip in all_computing_ips:
            send_assignment_info(computing_ip)
        for home_ip in home_ips:
            send_assignment_info(home_ip)
        for controller_ip in controller_ip_nondag:
            send_assignment_info(controller_ip)
    except:
        print('Not yet receive best compute node assignment!')

def send_controller_info(node_ip):
    """Send my task controller information to the compute node
    
    Args:
        node_ip (str): IP of the compute node
    """
    try:
        url = "http://" + node_ip + ":" + str(FLASK_SVC) + "/update_controller_map"
        params = {'controller_id_map':controller_id_map}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending controller message to flask server on computing node FAILED!!!")
        print(e)
        return "not ok"

def push_controller_map():
    """Push my task controller information to all the compute nodes
    """
    time.sleep(90)
    for computing_ip in all_computing_ips:
        send_controller_info(computing_ip)
    if BOKEH==3:    
        topic = 'msgoverhead_controller%s'%(self_task)
        msg = 'msgoverhead pricepush controller%s pushcontroller %d \n'%(self_task,len(all_computing_ips))
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)


    
def update_assignment_info_child():
    """
        Receive the best computing node for the task
    """
    
    try:
        print("Update best assignment info from parents")
        assignment_info = request.args.get('assignment_info').split('#')
        task_node_map[assignment_info[0]] = assignment_info[1]

    except Exception as e:
        print("Bad reception or failed processing in Flask for best assignment request: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/update_assignment_info_child', '/update_assignment_info_child', update_assignment_info_child)

def send_assignment_info(node_ip):
    """Send my current best compute node to the node given its IP
    
    Args:
        node_ip (str): IP of the node
    """
    try:
        print("Announce my current best computing node " + node_ip)
        url = "http://" + node_ip + ":" + str(FLASK_SVC) + "/receive_assignment_info"
        assignment_info = self_task + "#"+task_node_map[self_task]
        params = {'assignment_info': assignment_info}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        if BOKEH==3:    
            topic = 'msgoverhead_controller%s'%(self_task)
            msg = 'msgoverhead pricepush controller%s updatebest 1\n'%(self_task)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    except Exception as e:
        print("The computing node is not yet available. Sending assignment message to flask server on computing node FAILED!!!")
        print(e)
        return "not ok"

def update_assignment_info_to_child(node_ip):
    """Update my current best compute node to my children tasks
    
    Args:
        node_ip (str): IP of my children task
    """
    try:
        print("Announce my current best computing node to children " + node_ip)
        url = "http://" + node_ip + ":" + str(FLASK_SVC) + "/update_assignment_info_child"
        assignment_info = self_task + "#"+task_node_map[self_task]
        params = {'assignment_info': assignment_info}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending assignment message to flask server on child controller nodes FAILED!!!")
        print(e)
        return "not ok"

def announce_best_assignment_to_child():
    """Announce my current best assignment to all my children tasks
    """
    print('Announce best assignment to my children')
    for child_ip in child_nodes_ip_dag:
        update_assignment_info_to_child(child_ip)   
    if BOKEH==3:    
        topic = 'msgoverhead_controller%s'%(self_task)
        msg = 'msgoverhead pricepush controller%s sendassignmentchild %d\n'%(self_task,len(child_nodes_ip_dag))
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)

def push_first_assignment_map():
    """Waiting for the first assignment
    """
    while self_task not in task_node_map:
        default_best_node()
        print('Waiting for first best assignment for my task' + self_task)
        time.sleep(10) 
    
    print('Sucessfully assign the first best computing node')
    update_best_node()
    if 'home' not in child_nodes:
        announce_best_assignment_to_child()

def push_assignment_map():
    """Update assignment periodically
    """
    print('Updated assignment periodically')
    default_best_node()
    update_best_node()
    if 'home' not in child_nodes:
        announce_best_assignment_to_child()

def schedule_update_assignment(interval):
    """
    Schedulete the assignment update every interval
    
    Args:
        interval (int): chosen interval (minutes)
    
    """
    sched = BackgroundScheduler()
    sched.add_job(push_assignment_map,'interval',id='assign_id', minutes=interval, replace_existing=True)
    sched.start()


def send_runtime_profile(msg,taskname):
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
        for home_node_host_port in home_node_host_ports:
            url = "http://" + home_node_host_port + "/recv_runtime_profile"
            params = {'msg': msg, "work_node": taskname}
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

class TimedValue:

    def __init__(self):
        self._started_at = datetime.datetime.utcnow()

    def __call__(self):
        time_passed = datetime.datetime.utcnow() - self._started_at
        if time_passed.total_seconds() > (6*60-1): #scheduled price announce = 3 mins
            return True
        return False

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
    """
        -   Load all the Jupiter confuguration
        -   Load DAG information. 
        -   Prepare all of the tasks based on given DAG information. 
        -   Prepare the list of children tasks for every parent task
        -   Generating monitoring process for ``INPUT`` folder.
        -   Generating monitoring process for ``OUTPUT`` folder.
        -   If there are enough input files for the first task on the current node, run the first task. 

    """

    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global dag
    dag_file = '/centralized_scheduler/dag.txt'
    dag_info = k8s_read_dag(dag_file)
    dag = dag_info[1]


    global next_tasks_map,last_tasks_map, child_nodes, child_nodes_ip, home_ips,home_ids, home_ip_map
    next_tasks_map = dict()
    last_tasks_map = dict()

    
    for task in dag:
        next_tasks_map[task] = dag[task][2:]
        for last_task in dag[task][2:]:
            if last_task not in last_tasks_map:
                last_tasks_map[last_task] = [task]
            else:    
                last_tasks_map[last_task].append(task)




    child_nodes = os.environ['CHILD_NODES'].split(':')
    child_nodes_ip = os.environ['CHILD_NODES_IPS'].split(':')


    home_nodes = os.environ['HOME_NODE'].split(' ')
    home_ids = [x.split(':')[0] for x in home_nodes]
    home_ips = [x.split(':')[1] for x in home_nodes]
    home_ip_map = dict(zip(home_ids, home_ips))


    # Prepare transfer-runtime file:
    global runtime_sender_log, RUNTIME, TRANSFER, transfer_type
    RUNTIME = int(config['CONFIG']['RUNTIME'])
    TRANSFER = int(config['CONFIG']['TRANSFER'])

    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

    global app_name,app_option
    app_name = os.environ['APP_NAME']
    app_option = os.environ['APP_OPTION']


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

    global FLASK_SVC, FLASK_DOCKER, MONGO_PORT, username,password,ssh_port, num_retries, task_mul, count_dict,self_ip, all_nodes, all_nodes_ips


    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT  = int(config['PORT']['MONGO_DOCKER'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    self_ip     = os.environ['OWN_IP']
    all_nodes   = os.environ['ALL_NODES'].split(':')
    all_nodes_ips   = os.environ['ALL_NODES_IPS'].split(':')

    home_nodes = os.environ['HOME_NODE'].split(' ')
    home_ids = [x.split(':')[0] for x in home_nodes]
    home_ips = [x.split(':')[1] for x in home_nodes]


    global taskmap, taskname, taskmodule, filenames,files_out, home_node_host_ports
    global self_id, self_name, self_task, first_task
    global all_computing_nodes,all_computing_ips, num_computing_nodes, node_ip_map, controller_id_map

    configs = json.load(open('/centralized_scheduler/config.json'))
    taskmap = configs["taskname_map"][sys.argv[len(sys.argv)-1]]
    taskname = taskmap[0]
    if taskmap[1] == True:
        taskmodule = __import__(taskname)

    #target port for SSHing into a container
    filenames=[]
    files_out=[]
    self_name= os.environ['NODE_NAME']
    self_id  = os.environ['NODE_ID']
    self_task= os.environ['TASK']

    first_task = os.environ['FIRST_TASK']
    controller_id_map = self_task + ":" + self_id
    home_node_host_ports =  [x + ":" + str(FLASK_SVC) for x in home_ips]

    all_computing_nodes = os.environ["ALL_COMPUTING_NODES"].split(":")
    all_computing_ips = os.environ["ALL_COMPUTING_IPS"].split(":")
    num_computing_nodes = len(all_computing_nodes)
    node_ip_map = dict(zip(all_computing_nodes, all_computing_ips))



    update_interval = 1

    global dest_node_host_port_list
    dest_node_host_port_list = [ip + ":" + str(FLASK_SVC) for ip in all_computing_ips]

    global task_price_cpu, task_node_map, task_price_mem, task_price_queue, task_price_net
    manager = Manager()
    task_price_cpu = manager.dict()
    task_price_mem = manager.dict()
    task_price_queue = manager.dict()
    task_price_net = manager.dict()
    task_node_map = manager.dict()

    global pass_time
    pass_time = dict()
    

    global tasks, task_order, super_tasks, non_tasks
    tasks, task_order, super_tasks, non_tasks = get_taskmap()

    last_tasks_map[first_task] = []
    for home_id in home_ids:
        last_tasks_map[home_id] = last_tasks_map['home'] 
        task_node_map[home_id]  = home_id
        next_tasks_map[home_id] = [first_task]
        last_tasks_map[first_task].append(home_id)

    for task in super_tasks:
        task_node_map[task] = task   

    global child_nodes_dag, child_nodes_ip_dag

    child_nodes_dag = []
    child_nodes_ip_dag = []
    
    for idx, child in enumerate(child_nodes):

        if child not in super_tasks:
            child_nodes_dag.append(child)
            child_nodes_ip_dag.append(child_nodes_ip[idx])
    global controller_nondag, controller_ip_nondag
    controller_nondag = []
    controller_ip_nondag = []
    for idx, controller in enumerate(all_nodes):
        if controller in super_tasks:
            controller_nondag.append(controller)
            controller_ip_nondag.append(all_nodes_ips[idx])
    _thread.start_new_thread(push_controller_map,())
    _thread.start_new_thread(push_first_assignment_map,())
    _thread.start_new_thread(schedule_update_assignment,(update_interval,))

    web_server = MonitorRecv()
    web_server.run()

    if taskmap[1] == True:
        task_mul = manager.dict()
        count_dict = manager.dict()
        
    else:

        path_src = "/centralized_scheduler/" + taskname
        args = ' '.join(str(x) for x in taskmap[2:])

        if os.path.isfile(path_src + ".py"):
            cmd = "python3 -u " + path_src + ".py " + args          
        else:
            cmd = "sh " + path_src + ".sh " + args
        os.system(cmd)

if __name__ == '__main__':
    main()
