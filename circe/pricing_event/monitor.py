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




app = Flask(__name__)


global bottleneck
bottleneck = defaultdict(list)

def tic():
    return time.time()

def toc(t):
    texec = time.time() - t
    # print('Execution time is:'+str(texec))
    return texec

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
        # print('***************************************************')
        # print("Received pricing info")
        # t = tic()
        pricing_info = request.args.get('pricing_info').split('#')
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
        # print('Check price updated interval ')
        # print(node_name)
        pass_time[node_name] = TimedValue()
        # txec = toc(t)
        # bottleneck['receiveprice'].append(txec)
        # # print(np.mean(bottleneck['receiveprice']))
        # print('***************************************************')

    except Exception as e:
        print("Bad reception or failed processing in Flask for pricing announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_price_info', 'receive_price_info', receive_price_info)    


def default_best_node(source_node):
    # print('***************************************************')
    print('Select the current best node')
    # t = tic()
    w_net = 1 # Network profiling: longer time, higher price
    w_cpu = 100000 # Resource profiling : larger cpu resource, lower price
    w_mem = 100000 # Resource profiling : larger mem resource, lower price
    w_queue = 1 # Queue : currently 0
    # print('-----------------Current ratio')
    # print(w_mem)
    best_node = -1
    task_price_network= dict()
    # print('----------')
    # print(task_price_cpu)
    # print(task_price_mem)
    # print(task_price_queue)
    # print(task_price_net)
    # print(len(task_price_net))
    # print(source_node)
    # print('DEBUG')
    for (source, dest), price in task_price_net.items():
        if source == source_node:
            # print('hehehhehheheh')
            # print(source_node)
            task_price_network[dest]= price
    
    # print('uhmmmmmmm')
    # print(self_id)
    # print(self_task)
    # print(self_name)
    task_price_network[source_node] = 0 #the same node
    # print(task_price_network)
    # print(task_price_cpu)

    # print('------------3')
    # print('CPU utilization')
    # print(task_price_cpu)
    # print('Memory utilization')
    # print(task_price_mem)
    # print('Queue cost')
    # print(task_price_queue)
    # print('Network cost')
    # print(task_price_network)

    if len(task_price_network.keys())>1: #net(node,home) not exist
        #print('------------2')
        task_price_summary = dict()
        # print(task_price_cpu.items())
        # print(task_price_network)
        for item, p in task_price_cpu.items():
            # print('---')
            # print(item)
            # print(p)
            if item in home_ids: continue
            # print(task_price_cpu[item])
            # print(task_price_mem[item])
            # print(task_price_queue[item])
            # print(task_price_network[item])

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
        
        # print('Summary cost')
        # print(task_price_summary)
        best_node = min(task_price_summary,key=task_price_summary.get)
        # print(best_node)

        # txec = toc(t)
        # bottleneck['selectbest'].append(txec)
        # print(np.mean(bottleneck['selectbest']))
        # print('***************************************************')
    else:
        print('Task price summary is not ready yet.....') 
    return best_node

def predict_best_node(source_node):
    """Select the best node from price information of all nodes, either default or customized from user price file
    """
    #if PRICE_OPTION ==0: #default
    best_node = default_best_node(source_node)
    return best_node

def receive_best_assignment_request():
    try:
        # print('***************************************************')
        # print("------ Receive request of best assignment")
        # t = tic()
        home_id = request.args.get('home_id')
        source_node = request.args.get('node_name')
        file_name = request.args.get('file_name')
        source_key = request.args.get('key')
        # print('***')
        # print(home_id)
        # print(source_node)
        # print(file_name)
        # print(source_key)
        best_node = predict_best_node(source_node)
        # print(best_node)
        # print('******')
        # txec = toc(t)
        # bottleneck['receiveassign'].append(txec)
        # print(np.mean(bottleneck['receiveassign']))
        # print('***************************************************')
        # print('Announce ---')
        
        announce_best_assignment(home_id,best_node, source_node, file_name,source_key)
        
    except Exception as e:
        print("Sending assignment message to flask server on computing node FAILED!!!")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/receive_best_assignment_request', 'receive_best_assignment_request', receive_best_assignment_request)

def announce_best_assignment(home_id,best_node, source_node, file_name,source_key):
    try:
        # print('***************************************************')
        # print("Announce the best computing node for my task:" + self_task)
        # t = tic()
        # print(node_ip_map)
        # print(source_node)
        # print(self_task)
        # print(best_node)
        # print(file_name)
        # print(source_key)
        # print(node_ip_map[source_key])
        url = "http://" + node_ip_map[source_key] + ":" + str(FLASK_SVC) + "/receive_best_assignment"
        # print(url)
        params = {'home_id':home_id,'task_name':self_task,'file_name':file_name,'best_computing_node':best_node}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        # print(req)
        res = urllib.request.urlopen(req)
        # print(res)
        res = res.read()
        res = res.decode('utf-8')
        # print(res)

        # txec = toc(t)
        # bottleneck['announcebest'].append(txec)
        # # print(np.mean(bottleneck['announcebest']))
        # print('***************************************************')
    except Exception as e:
        print("Sending assignment information to flask server on computing nodes FAILED!!!")
        print(e)
        return "not ok"


def send_controller_info(node_ip):
    try:
        # print('***************************************************')
        # t = tic()
        # t1 = time.time()
        # print("Announce my current node mapping to " + node_ip)
        url = "http://" + node_ip + ":" + str(FLASK_SVC) + "/update_controller_map"
        params = {'controller_id_map':controller_id_map}
        # thread = Worker(url,params)
        # thread.start()
        # print(time.time()-t1)
        # t1 = time.time()
        params = urllib.parse.urlencode(params)
        # print(time.time()-t1)
        # t1 = time.time()
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        # print(time.time()-t1)
        # t1 = time.time()
        res = urllib.request.urlopen(req)
        # print(time.time()-t1)
        # t1 = time.time()
        res = res.read()
        # print(time.time()-t1)
        # t1 = time.time()
        res = res.decode('utf-8')
        # print(time.time()-t1)
        # t1 = time.time()
        # txec = toc(t)
        # bottleneck['sendcontroller'].append(txec)
        # print(time.time()-t1)
        # print(np.mean(bottleneck['sendcontroller']))
        # print('***************************************************')
    except Exception as e:
        print("Sending controller message to flask server on computing node FAILED!!!")
        print(e)
        return "not ok"

def push_controller_map():
    time.sleep(90)
    # print('***************************************************')
    # print('Send all controller information')
    # t = tic()
    for computing_ip in all_computing_ips:
        # t1 = time.time()
        # print(computing_ip)
        send_controller_info(computing_ip)
        # print(time.time()-t1)
    # txec = toc(t)
    # print('***************************************************')

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
        # app.run(host='0.0.0.0', port=FLASK_DOCKER)



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
    # print(taskmap)
    taskname = taskmap[0]
    # print(taskname)

    global tasks, task_order, super_tasks, non_tasks
    tasks, task_order, super_tasks, non_tasks = get_taskmap()

    global controller_nondag, controller_ip_nondag
    controller_nondag = []
    controller_ip_nondag = []

    #include home?
    
    global all_nodes_list, all_nodes_ips_list
    all_nodes_list   = os.environ['ALL_NODES'].split(':')
    all_nodes_ips_list   = os.environ['ALL_NODES_IPS'].split(':')

    all_computing_nodes = os.environ["ALL_COMPUTING_NODES"].split(":")
    all_computing_ips = os.environ["ALL_COMPUTING_IPS"].split(":")
    all_nodes = all_computing_nodes + home_ids
    all_nodes_ips = all_computing_ips + home_ips

    # print(all_nodes)
    # print(super_tasks)
    for idx, controller in enumerate(all_nodes_list):
        if controller in super_tasks:
            # print(controller)
            # print(all_nodes_ips_list[idx])
            controller_nondag.append(controller)
            controller_ip_nondag.append(all_nodes_ips_list[idx])

            all_nodes.append(controller)
            all_nodes_ips.append(all_nodes_ips_list[idx])
            
    # print(controller_nondag) 
    # print(controller_ip_nondag)

    if taskmap[1] == True:
        taskmodule = __import__(taskname)

    #target port for SSHing into a container
    filenames=[]
    files_out=[]
    self_name= os.environ['NODE_NAME']
    self_id  = os.environ['NODE_ID']
    self_task= os.environ['TASK']
    #controller_id_map = self_task + ":" + self_id
    controller_id_map = self_task + "#" + self_id
    #update_interval = 10 #minutes
    home_node_host_ports =  [x + ":" + str(FLASK_SVC) for x in home_ips]

    

    node_ip_map = dict(zip(all_nodes, all_nodes_ips))

    # print('************************** DEBUG 3')
    # print(node_ip_map)


    

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
    task_node_summary['current_best_node'] = self_id

    


    _thread.start_new_thread(push_controller_map,())
    

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
    
