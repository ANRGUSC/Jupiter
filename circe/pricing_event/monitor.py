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
import cProfile
import numpy as np
from collections import defaultdict
import paho.mqtt.client as mqtt




app = Flask(__name__)


def tic():
    return time.time()

def toc(t):
    texec = time.time() - t
    return texec

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


def default_best_node(source_node):
    print('Select the current best node')
    starttime = time.time()
    w_net = 1 # Network profiling: longer time, higher price
    w_cpu = 1 # Resource profiling : larger cpu resource, lower price
    w_mem = 1 # Resource profiling : larger mem resource, lower price
    w_queue = 1 # Queue : currently 0
    best_node = -1
    task_price_network= dict()
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
        
        best_node = min(task_price_summary,key=task_price_summary.get)
        mappinglatency = time.time() - starttime   
        if BOKEH==3:    
            topic = 'mappinglatency_%s'%(app_option)
            msg = 'mappinglatency priceevent controller%s %s %f\n'%(self_task,app_name,mappinglatency)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    else:
        print('Task price summary is not ready yet.....') 
    return best_node

def predict_best_node(source_node):
    """Select the best node from price information of all nodes, either default or customized from user price file
    """
    best_node = default_best_node(source_node)
    return best_node

def receive_best_assignment_request():
    try:
        print("------ Receive request of best assignment")
        home_id = request.args.get('home_id')
        source_node = request.args.get('node_name')
        file_name = request.args.get('file_name')
        source_key = request.args.get('key')
        key = (home_id,file_name)
        if key in task_node_summary and task_node_summary[key]!=-1:
            print('Already existed in task node mapping')
            best_node = task_node_summary[key]
        else:
            print('Not yet existed in task node mapping')
            best_node = predict_best_node(source_node)
            task_node_summary[key] = best_node
        announce_best_assignment(home_id,best_node, source_node, file_name,source_key)
        
    except Exception as e:
        print("Sending assignment message to flask server on computing node FAILED!!!")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/receive_best_assignment_request', 'receive_best_assignment_request', receive_best_assignment_request)

def announce_best_assignment(home_id,best_node, source_node, file_name,source_key):
    try:
        print("Announce the best computing node for my task " + self_task+ " is " + best_node)
        url = "http://" + node_ip_map[source_key] + ":" + str(FLASK_SVC) + "/receive_best_assignment"
        params = {'home_id':home_id,'task_name':self_task,'file_name':file_name,'best_computing_node':best_node}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')

        if BOKEH==3:    
            topic = 'msgoverhead_controller%s'%(self_task)
            msg = 'msgoverhead priceevent controller%s announcebest %s 1\n'%(self_task,source_node)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    except Exception as e:
        print("Sending assignment information to flask server on computing nodes FAILED!!!")
        print(e)
        return "not ok"


def send_controller_info(node_ip):
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
    time.sleep(90)
    for computing_ip in all_computing_ips:
        send_controller_info(computing_ip)
    if BOKEH==3:    
        topic = 'msgoverhead_controller%s'%(self_task)
        msg = 'msgoverhead priceevent controller%s pushcontroller %d \n'%(self_task,len(all_computing_ips))
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)

class TimedValue:

    def __init__(self):
        self._started_at = datetime.datetime.utcnow()

    def __call__(self):
        time_passed = datetime.datetime.utcnow() - self._started_at
        if time_passed.total_seconds() > (6*60-1): #scheduled price announce = 3 mins
            return True
        return False

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

class Worker(threading.Thread):

    def __init__(self, url,values):
        self.values = values
        self.url = url
        threading.Thread.__init__(self)

    def run(self):
        data = urllib.parse.urlencode(self.values)
        encoded_data = data.encode('ascii')
        req = urllib.request.Request(self.url, encoded_data)
        response = urllib.request.urlopen(req)
        the_page = response.read()

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER,threaded=True)



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
    
    # Prepare transfer-runtime file:
    global runtime_sender_log, RUNTIME, TRANSFER, transfer_type
    RUNTIME = int(config['CONFIG']['RUNTIME'])
    TRANSFER = int(config['CONFIG']['TRANSFER'])

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

    global FLASK_SVC, FLASK_DOCKER, MONGO_PORT, username,password,ssh_port, num_retries, task_mul, count_dict,self_ip, home_ips, home_ids


    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT  = int(config['PORT']['MONGO_DOCKER'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    self_ip     = os.environ['OWN_IP']
    home_nodes = os.environ['HOME_NODE'].split(' ')
    home_ids = [x.split(':')[0] for x in home_nodes]
    home_ips = [x.split(':')[1] for x in home_nodes]


    global taskmap, taskname, taskmodule, filenames,files_out, home_node_host_ports
    global all_nodes, all_nodes_ips, self_id, self_name, self_task
    global all_computing_nodes,all_computing_ips, node_ip_map, controller_id_map

    configs = json.load(open('/centralized_scheduler/config.json'))
    taskmap = configs["taskname_map"][sys.argv[len(sys.argv)-1]]
    taskname = taskmap[0]

    global tasks, task_order, super_tasks, non_tasks
    tasks, task_order, super_tasks, non_tasks = get_taskmap()

    global controller_nondag, controller_ip_nondag
    controller_nondag = []
    controller_ip_nondag = []
    
    global all_nodes_list, all_nodes_ips_list
    all_nodes_list   = os.environ['ALL_NODES'].split(':')
    all_nodes_ips_list   = os.environ['ALL_NODES_IPS'].split(':')

    all_computing_nodes = os.environ["ALL_COMPUTING_NODES"].split(":")
    all_computing_ips = os.environ["ALL_COMPUTING_IPS"].split(":")
    all_nodes = all_computing_nodes + home_ids
    all_nodes_ips = all_computing_ips + home_ips

    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

    for idx, controller in enumerate(all_nodes_list):
        if controller in super_tasks:
            print(controller)
            print(all_nodes_ips_list[idx])
            controller_nondag.append(controller)
            controller_ip_nondag.append(all_nodes_ips_list[idx])

            all_nodes.append(controller)
            all_nodes_ips.append(all_nodes_ips_list[idx])

    if taskmap[1] == True:
        taskmodule = __import__(taskname)

    #target port for SSHing into a container
    filenames=[]
    files_out=[]
    self_name= os.environ['NODE_NAME']
    self_id  = os.environ['NODE_ID']
    self_task= os.environ['TASK']
    controller_id_map = self_task + "#" + self_id
    home_node_host_ports =  [x + ":" + str(FLASK_SVC) for x in home_ips]
    node_ip_map = dict(zip(all_nodes, all_nodes_ips))

    

    global dest_node_host_port_list
    dest_node_host_port_list = [ip + ":" + str(FLASK_SVC) for ip in all_computing_ips]

    global task_price_cpu, task_node_summary, task_price_mem, task_price_queue, task_price_net
    manager = Manager()
    task_price_cpu = manager.dict()
    task_price_mem = manager.dict()
    task_price_queue = manager.dict()
    task_price_net = manager.dict()
    task_node_summary = manager.dict()

    global pass_time
    pass_time = dict()

    # Set up default value for task_node_summary: the task controller will perform the tasks also

    _thread.start_new_thread(push_controller_map,())
    

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
    
