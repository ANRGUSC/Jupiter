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
        # print(pricing_info)
        #Network, CPU, Memory, Queue
        node_name = pricing_info[0]

        task_price_cpu[node_name] = float(pricing_info[1])
        task_price_mem[node_name] = float(pricing_info[2])
        task_price_queue[node_name] = float(pricing_info[3].split('$')[0])
        price_net_info = pricing_info[3].split('$')[1:]
        # print(price_net_info)
        for price in price_net_info:
            # print(price)
            # print(node_name)
            # print(price.split('%')[0])
            # print(price.split('%')[1])
            task_price_net[node_name,price.split('%')[0]] = float(price.split('%')[1])
        # print(task_price_net)
        # print('Check price updated interval ')
        # print(node_name)
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
    w_net = 1 # Network profiling: longer time, higher price
    w_cpu = 1 # Resource profiling : larger cpu resource, lower price
    w_mem = 1 # Resource profiling : larger mem resource, lower price
    w_queue = 1 # Queue : currently 0
    best_node = -1
    task_price_network= dict()
    # print('----------')
    # print(task_price_cpu)
    # print(task_price_mem)
    # print(task_price_queue)
    # print(task_price_net)
    # print(len(task_price_net))
    # print(source_node)

    # case that have multiple parents: temporarily choose the lowest index???
    print('----------------------------??????')
    print(last_tasks_map)
    print(self_task)
    print(last_tasks_map[self_task])
    temp_parents = [x for x in last_tasks_map[self_task] if x not in super_tasks]

    print(temp_parents)
    # print(task_node_map)
    
    if temp_parents[0] not in task_node_map:
    #if last_tasks_map[self_task][0] not in task_node_map:
        print('Parent tasks not available yet!!!!')
    else:
        print('Parent tasks')
        # print(last_tasks_map[self_task])
        # print(last_tasks_map[self_task][0])
        source_node = task_node_map[temp_parents[0]]
        # source_node = task_node_map[last_tasks_map[self_task][0]]
        print('Current best compute node of parent tasks')
        print(source_node)
        print('DEBUG')
        print(task_price_net)
        for (source, dest), price in task_price_net.items():
            if source == source_node:
                # print('hehehhehheheh')
                # print(source_node)
                task_price_network[dest]= price
        
        task_price_network[source_node] = 0 #the same node
        print('uhmmmmmmm')
        # print(task_price_network)
        # print(task_price_cpu)
        # print(self_id)
        # print(self_task)
        # print(self_name)
        # print(task_price_network.keys())
        # print(task_price_cpu.keys())
        # print(len(task_price_network.keys()))
        # print(len(task_price_cpu.keys()))
        print('CPU utilization')
        print(task_price_cpu)
        print('Memory utilization')
        print(task_price_mem)
        print('Queue cost')
        print(task_price_queue)
        print('Network cost')
        print(task_price_network)
        print(task_price_network.keys())
        if len(task_price_network.keys())>1: #net(node,home) not exist
            
            # print('------------2')
            # print(task_price_network)
            print('Available task price information')
            task_price_summary = dict()
            # print(task_price_cpu.items())
            # print(task_price_network)
            # print(home_ids)
            for item, p in task_price_cpu.items():
                # print('---')
                # print(item)
                # print(p)
                if item in home_ids: continue
                #check time pass
                # print('Check passing time------------------')
                # print(item)

                test = pass_time[item].__call__()
                # print(test)
                if test==True: 
                    # print('Yeahhhhhhhhhhhhhhhhhhhhhh')
                    task_price_network[item] = float('Inf')
                # print(task_price_network[item])
                task_price_summary[item] = task_price_cpu[item]*w_cpu +  task_price_mem[item]*w_mem + task_price_queue[item]*w_queue + task_price_network[item]*w_net
                # print(task_price_summary[item])
            # print('------------3')
            
            print('Summary cost')
            print(task_price_summary)
            if task_price_summary:
                #print(task_price_summary)
                best_node = min(task_price_summary,key=task_price_summary.get)
                print(best_node)
                task_node_map[self_task] = best_node   
        else:
            print('Task price summary is not ready yet.....') 
        
    
    



def update_best_node():
    """Select the best node from price information of all nodes, either default or customized from user price file
    """
    # if PRICE_OPTION ==0: #default
    #     # default_best_node()
    #     default_best_node()
    # else:
    #     customized_parameters_best_node()
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

def schedule_update_price(interval):
    """
        Send controller id node mapping to all the computing nodes
    """
    sched = BackgroundScheduler()
    sched.add_job(update_best_node,'interval',id='push_id', minutes=interval, replace_existing=True)
    sched.start()

def send_controller_info(node_ip):
    """Send my task controller information to the compute node
    
    Args:
        node_ip (str): IP of the compute node
    """
    try:
        print("Announce my current node mapping to " + node_ip)
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


    
def update_assignment_info_child():
    """
        Receive the best computing node for the task
    """
    
    try:
        print("Update best assignment info from parents")
        assignment_info = request.args.get('assignment_info').split('#')
        print("Received assignment info")
        task_node_map[assignment_info[0]] = assignment_info[1]
        # print(task_node_map)

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
        print(assignment_info)
        params = {'assignment_info': assignment_info}
        params = urllib.parse.urlencode(params)
        print(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        print(req)
        res = urllib.request.urlopen(req)
        print(res)
        res = res.read()
        print(res)
        res = res.decode('utf-8')
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
        #print(assignment_info)
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
    print(child_nodes_dag)
    print(child_nodes_ip_dag)
    for child_ip in child_nodes_ip_dag:
        print(child_ip)
        update_assignment_info_to_child(child_ip)   

def push_first_assignment_map():
    """Waiting for the first assignment
    """
    print('Waiting for the first assignment')
    
    # print(task_node_map)
    while self_task not in task_node_map:
        # print(task_node_map)
        default_best_node()
        # push_assignment_map()
        print('Waiting for first best assignment for my task' + self_task)
        time.sleep(10) 
    
    print('Sucessfully assign the first best computing node')
    print(task_node_map)
    update_best_node()
    announce_best_assignment_to_child()

def push_assignment_map():
    """Update assignment periodically
    """
    print('Updated assignment periodically')
    default_best_node()
    print(task_node_map)
    print(self_task)
    print(all_computing_ips)
    print(all_computing_nodes)
    if self_task in task_node_map:
        print('*********************************************')
        print('update compute nodes')
        print(all_computing_nodes)
        for computing_ip in all_computing_ips:
            send_assignment_info(computing_ip)
        print('*********************************************')
        print('home nodes')
        print(home_ips)
        print(home_ids)
        for home_ip in home_ips:
            send_assignment_info(home_ip)
        print('*********************************************')
        print('controller non_dag')
        print(controller_nondag)
        for controller_ip in controller_ip_nondag:
            send_assignment_info(controller_ip)
        announce_best_assignment_to_child()
    else:
        print('Current best computing node not yet assigned!')

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
        print("Sending message", msg)
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


    # Price calculation methods
    # global PRICE_OPTION
    # PRICE_OPTION          = int(config['CONFIG']['PRICE_OPTION'])


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
    # print(taskmap)
    taskname = taskmap[0]
    # print(taskname)
    if taskmap[1] == True:
        taskmodule = __import__(taskname)

    #target port for SSHing into a container
    filenames=[]
    files_out=[]
    self_name= os.environ['NODE_NAME']
    self_id  = os.environ['NODE_ID']
    self_task= os.environ['TASK']

    first_task = os.environ['FIRST_TASK']
    # print(first_task)
    controller_id_map = self_task + ":" + self_id
    #update_interval = 10 #minutes
    home_node_host_ports =  [x + ":" + str(FLASK_SVC) for x in home_ips]

    all_computing_nodes = os.environ["ALL_COMPUTING_NODES"].split(":")
    all_computing_ips = os.environ["ALL_COMPUTING_IPS"].split(":")
    num_computing_nodes = len(all_computing_nodes)
    node_ip_map = dict(zip(all_computing_nodes, all_computing_ips))



    update_interval = 3 

    global dest_node_host_port_list
    dest_node_host_port_list = [ip + ":" + str(FLASK_SVC) for ip in all_computing_ips]

    # global task_price_summary, task_node_map
    # manager = Manager()
    # task_price_summary = manager.dict()
    # task_node_map = manager.dict()

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
        print(task)
        task_node_map[task] = task   

    global child_nodes_dag, child_nodes_ip_dag

    child_nodes_dag = []
    child_nodes_ip_dag = []
    

    print('---------------------------------------------- DEBUG')
    # print(child_nodes)
    for idx, child in enumerate(child_nodes):
        print(idx)
        print(child)
        if child not in super_tasks:
            child_nodes_dag.append(child)
            child_nodes_ip_dag.append(child_nodes_ip[idx])

    print(child_nodes_dag)
    print(child_nodes_ip_dag)
    
    global controller_nondag, controller_ip_nondag
    controller_nondag = []
    controller_ip_nondag = []

    print(all_nodes)
    print(super_tasks)
    for idx, controller in enumerate(all_nodes):
        if controller in super_tasks:
            print(controller)
            controller_nondag.append(controller)
            controller_ip_nondag.append(all_nodes_ips[idx])

    print(controller_nondag) 
    print(controller_ip_nondag)

    
    _thread.start_new_thread(push_controller_map,())
    _thread.start_new_thread(push_first_assignment_map,())
    _thread.start_new_thread(schedule_update_price,(update_interval,))
    _thread.start_new_thread(schedule_update_assignment,(update_interval,))

    web_server = MonitorRecv()
    web_server.run()
    #web_server.start()

    if taskmap[1] == True:
        task_mul = manager.dict()
        count_dict = manager.dict()
        

        # #monitor INPUT as another process
        # w=Watcher()
        # w.run()

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