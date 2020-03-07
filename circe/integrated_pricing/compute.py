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
import paho.mqtt.client as mqtt
import pyinotify

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

def cal_file_size(file_path):
    """Return the file size in bytes
    
    Args:
        file_path (str): The file path
    
    Returns:
        float: file size in bytes
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return file_info.st_size * 0.008

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

    global manager,task_mul, count_mul, queue_mul, size_mul,next_mul, files_mul, controllers_id_map, pass_time
    

    manager = Manager()
    task_mul = manager.dict() # list of incoming tasks and files
    count_mul = manager.dict() # number of input files required for each task
    queue_mul = manager.dict() # tasks which have not yet been processed
    size_mul  = manager.dict() # total input size of each incoming task and file
    next_mul = manager.dict() # information of next node (IP,username,pass) fo the current file
    files_mul = manager.dict()
    controllers_id_map = manager.dict()
    pass_time = manager.dict()

    global start_times, mapping_times, mapping_input_id
    start_times = manager.dict()
    mapping_times = manager.list()
    mapping_input_id = manager.dict()

    global local_task_node_map, global_task_node_map
    local_task_node_map = manager.dict()
    global_task_node_map = manager.dict()
    

    global task_price_cpu, task_price_mem, task_price_queue, task_price_net, my_task_price_net
    task_price_cpu = manager.dict()
    task_price_mem = manager.dict()
    task_price_queue = manager.dict()
    task_price_net = manager.dict()
    my_task_price_net = manager.dict()

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

    global graph,top_order_task
    graph= Graph(task_order)
    for src in tasks:
        if len(tasks[src])==0: continue
        for dest in tasks[src]:
            graph.addEdge(src,dest) 
    top_order_task = graph.topologicalSort() 

    last_tasks_map[os.environ['CHILD_NODES']] = []
    for home_id in home_ids:
        last_tasks_map[home_id] = last_tasks_map['home'] 
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


    
# NEW: update assignment 
def send_assignment_info(node_ip,task_name,best_node):
    """Send my current best compute node to the node given its IP
    
    Args:
        node_ip (str): IP of the node
    """
    try:
        print("Announce my current best computing node " + node_ip)
        url = "http://" + node_ip + ":" + str(FLASK_SVC) + "/receive_assignment_info"
        assignment_info = self_name+"#"+task_name + "#"+best_node
        params = {'assignment_info': assignment_info}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        if BOKEH==3:    
            topic = 'msgoverhead_%s'%(self_name)
            msg = 'msgoverhead priceintegrated %s updatebest 1\n'%(self_name)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    except Exception as e:
        print("The computing node is not yet available. Sending assignment message to flask server on computing node FAILED!!!")
        print(e)
        return "not ok"

def push_assignment_map():
    """Update assignment periodically
    """
    print('Updated assignment periodically')
    starttime = time.time()
    for task in tasks:
        best_node = new_predict_best_node(task)
        local_task_node_map[self_name,task] = best_node

    task_list = ''
    best_list = ''
    t0 = 0
    for task in tasks:
        if local_task_node_map[self_name,task]==-1:
            print('Best node has not been provided yet')
            break
        task_list = task_list+':'+task
        best_list = best_list+':'+local_task_node_map[self_name,task]
        t0 = t0+1
    task_list = task_list[1:]
    best_list = best_list[1:]
    
    if t0 == len(tasks):
        localmappingtime = time.time()-starttime
        if BOKEH==3:    
            topic = 'mappinglatency_%s'%(appoption)
            msg = 'mappinglatency priceintegrated compute%s %s %f\n'%(self_name,appname,localmappingtime)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
            starttime = time.time()

        for computing_ip in combined_ips:
            send_assignment_info(computing_ip,task_list,best_list)
    else:
        print('Not yet assignment!')

def schedule_update_assignment(interval):
    """
    Schedulete the assignment update every interval
    
    Args:
        interval (int): chosen interval (minutes)
    
    """
    sched = BackgroundScheduler()
    sched.add_job(push_assignment_map,'interval',id='assign_id', minutes=interval, replace_existing=True)
    sched.start()

def schedule_update_global(interval):
    """
    Schedulete the assignment update every interval
    
    Args:
        interval (int): chosen interval (minutes)
    
    """
    sched = BackgroundScheduler()
    sched.add_job(update_global_assignment,'interval',id='assign_id', minutes=interval, replace_existing=True)
    sched.start()



def update_global_assignment():
    print('Trying to update global assignment')
    starttime = time.time()
    m = (len(computing_nodes)+1)*len(tasks) # (all_compute & home,all_task)
    a = dict(local_task_node_map)
    if len(a)<m:
        print('Not yet fully loaded local information')
    else: 
        print('Fully loaded information')
        print('Mapping time')
        mapping_times.append(time.time())
        for home in home_ids:
            for task in top_order_task:
                if task==first_task:
                    global_task_node_map[len(mapping_times)-1,home,first_task]=local_task_node_map[home,first_task]
                else:
                    if len(last_tasks_map[task])==1:
                        prev_node = global_task_node_map[len(mapping_times)-1,home,last_tasks_map[task][0]]
                        global_task_node_map[len(mapping_times)-1,home,task] = local_task_node_map[prev_node,task]
                    else:
                        tmp_node_list =[]
                        for prev_task in last_tasks_map[task]:
                            prev_node = global_task_node_map[len(mapping_times)-1,home,prev_task]
                        last_tasks_map[task].sort()
                        chosen_task = last_tasks_map[task][0]
                        chosen_prev = global_task_node_map[len(mapping_times)-1,home,chosen_task]
                        global_task_node_map[len(mapping_times)-1,home,task] = local_task_node_map[chosen_prev,task]

    globalmappingtime = time.time()-starttime


    if BOKEH==3:    
        topic = 'mappinglatency_%s'%(appoption)
        msg = 'mappinglatency priceintegrated compute%s %s %f\n'%(self_name,appname,globalmappingtime)
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)

def receive_assignment_info():
    """
        Receive corresponding best nodes from the corresponding computing node
    """
    try:
        assignment_info = request.args.get('assignment_info').split('#')
        print("Received assignment info")
        task_list = assignment_info[1].split(':')
        best_list = assignment_info[2].split(':')
        for idx,task in enumerate(task_list):
            local_task_node_map[assignment_info[0],task] = best_list[idx]
    except Exception as e:
        print("Bad reception or failed processing in Flask for assignment announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_assignment_info', 'receive_assignment_info', receive_assignment_info)

def update_exec_profile_file():
    """Update the execution profile from the home execution profiler's MongoDB and store it in text file.
    """

    execution_info = []
    num_profilers = 0
    conn = False
    available_data = False
    print('Trying to update execution profiler')
    while not conn:
        try:
            client_mongo = MongoClient('mongodb://'+exec_home_ip+':'+str(MONGO_SVC)+'/')
            db = client_mongo.execution_profiler
            conn = True
        except:
            print('Error connection')
            time.sleep(5)
    while not available_data:
        try:
            logging =db[self_name].find()
            available_data = True
        except:
            print('Execution information for the current node is not ready!!!')
            time.sleep(5)

    c = 0
    for record in logging:
        # Node ID, Task, Execution Time, Output size
        info_to_csv=[record['Task'],record['Duration [sec]'],str(record['Output File [Kbit]'])]
        execution_info.append(info_to_csv)
        c = c+1
    print('Execution information has already been provided')
    with open('execution_log.txt','w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(execution_info)
    if BOKEH==3:    
        topic = 'msgoverhead_%s'%(self_name)
        msg = 'msgoverhead priceintegrated compute%s updateexec %d\n'%(self_name,c)
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    return


def get_updated_execution_profile():
    """Get updated execution information from text file
    """

    with open('execution_log.txt','r') as f:
        reader = csv.reader(f)
        execution = list(reader)
    # fix non-DAG tasks (temporary approach)
    # execution_info = []
    # for row in execution:
    #     if row[0]!='home':
    #         execution_info.append(row)
    #     else:
    #         print(row)
    #         if row[1] in super_tasks:
    #             for node in node_list:
    #                 execution_info.append([node,row[1],row[2],row[3]]) # to copy the home profiler data for the non dag task for each processor.
    # print(execution_info)
    execution_info = {}
    for row in execution:
        execution_info[row[0]] = [float(row[1]),float(row[2])]
    return execution_info

def get_updated_network_profile():
    """Get updated network information from the network profilers
    """
    network_info = dict()        
    try:
        client_mongo = MongoClient('mongodb://'+self_profiler_ip+':'+str(MONGO_SVC)+'/')
        db = client_mongo.droplet_network_profiler
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
        if num_nb == -1:
            print('--- Network profiler mongoDB not yet prepared')
            return network_info
        num_rows = db[self_profiler_ip].count() 
        if num_rows < num_nb:
            print('--- Network profiler regression info not yet loaded into MongoDB!')
            return network_info
        logging =db[self_profiler_ip].find().skip(db[self_profiler_ip].count()-num_nb)  
        c=0
        for record in logging:
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            network_info[ip_profilers_map[record['Destination[IP]']]] = str(record['Parameters'])
            c = c+1
        print('Retrieve network information')
        if BOKEH==3:    
            topic = 'msgoverhead_%s'%(self_name)
            msg = 'msgoverhead priceintegrated compute%s updatenetwork %d\n'%(self_name,c)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
        return network_info
    except Exception as e:
        print("Network request failed. Will try again, details: " + str(e))
        return -1
        

def get_updated_resource_profile():
    """Collect the resource profile from local MongoDB peer
    """
    resource_info = {}
    try:
        for ip in profiler_ip:
            print('Check Resource Profiler IP: '+ip)
            client_mongo = MongoClient('mongodb://'+ip+':'+str(MONGO_SVC)+'/')
            db = client_mongo.central_resource_profiler
            collection = db.collection_names(include_system_collections=False)
            logging =db[ip].find().skip(db[ip].count()-1)
            for record in logging:
                resource_info[ip_profilers_map[ip]]={'memory':record['memory'],'cpu':record['cpu'],'last_update':record['last_update']}

        print("Resource profiles: ", resource_info)
        if BOKEH==3:    
            topic = 'msgoverhead_%s'%(self_name)
            msg = 'msgoverhead priceintegrated compute%s updateresource %d\n'%(self_name,len(resource_info))
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
        return resource_info
    except Exception as e:
        print("Resource request failed. Will try again, details: " + str(e))
        return -1

def price_aggregate():
    """Calculate price required to perform the task based on network information, resource information, execution information and task queue size and sample size
    
    Returns:
        float: calculated price
    
    Args:
        task_name (str): Name of current task
    """

    # Default values
    price = dict()
    price['network'] = sys.maxsize
    price['cpu'] = sys.maxsize
    price['memory'] = sys.maxsize
    price['queue'] = 0

    """
    Input information:
        - Resource information: resource_info
        - Network information: network_info
        - Task queue: task_mul
        - Execution information: execution_info
    """

    try:
        
        print(' Retrieve all input information: ')
        execution_info = get_updated_execution_profile()
        resource_info = get_updated_resource_profile()
        network_info = get_updated_network_profile()
        # test_size = cal_file_size('/centralized_scheduler/1botnet.ipsum')
        price['memory'] = float(resource_info[self_name]["memory"])
        price['cpu'] = float(resource_info[self_name]["cpu"])
        if task_queue_size > 0: #not infinity 
            if len(queue_mul)==0:
                print('empty queue, no tasks are waiting')
            else:
                queue_dict = dict(queue_mul)
                queue_task = [k for k,v in queue_dict.items() if v == False]
                size_dict = dict(size_mul)
                queue_size =  [size_dict[k] for k in queue_dict.keys()] 
                for idx,task_info in enumerate(queue_task):
                    #TO_DO: sum or max
                    price['queue'] = queue_cost + execution_info[task_info[0]][0]* queue_size[idx] / test_output
        price['network'] = dict()

        for task in tasks:
            if task in home_ids: continue
            if task in super_tasks: continue 
            if task in non_tasks: continue 
            test_output = sample_size
            print('Price aggregation')
            tmp_price = sys.maxsize
            tmp_node = -1
            for node in network_info:
                if node in home_ids:
                    pass
                else:
                    computing_params = network_info[node].split(' ')
                    computing_params = [float(x) for x in computing_params]
                    
                    p = (computing_params[0] * test_output * test_output) + (computing_params[1] * test_output) + computing_params[2]
                    my_task_price_net[(task,node)] = p
                    if p < tmp_price:
                        tmp_price = p
                        tmp_node = node

            price['network'][task] = str(tmp_price)
        print('Overall price:')
        print(price)
        return price
             
    except:
        print('Error reading input information to calculate the price')
        
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
            task_price_net[node_name,price.split(':')[0]] = float(price.split(':')[1])
        pass_time[node_name] = TimedValue()

    except Exception as e:
        print("Bad reception or failed processing in Flask for pricing announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_price_info', 'receive_price_info', receive_price_info) 


def new_predict_best_node(task_name):
    w_net = 1 # Network profiling: longer time, higher price
    w_cpu = 1 # Resource profiling : larger cpu resource, lower price
    w_mem = 1 # Resource profiling : larger mem resource, lower price
    w_queue = 1 # Queue : currently 0
    best_node = -1
    task_price_network= dict()
    for (source, task), price in task_price_net.items():
        if task == task_name:
            task_price_network[source]= float(task_price_net[source,task])

    
    min_value = sys.maxsize

    for tmp_node_name in task_price_network:
        cur_delay = task_price_network[tmp_node_name]
        if cur_delay < min_value:
            min_value = cur_delay

    threshold = 15
    valid_nodes = []
    # get all the nodes that satisfy: time < tmin * threshold
    for tmp_node_name in task_price_network:
        if task_price_network[tmp_node_name] < min_value * threshold:
            valid_nodes.append(tmp_node_name)

    task_price_summary = dict()
    min_value = sys.maxsize
    result_node_name = ''
    for item in valid_nodes:
        tmp_net = task_price_network[item]
        tmp_cpu = sys.maxsize
        tmp_memory = sys.maxsize

        task_price_summary[item] = task_price_cpu[item]*w_cpu +  task_price_mem[item]*w_mem + task_price_queue[item]*w_queue + task_price_network[item]*w_net
    
    print('Task price summary')
    print(task_price_summary)
    try:
        best_node = min(task_price_summary,key=task_price_summary.get)
        print('Best node for '+task_name + ' is ' +best_node)
        return best_node
    except Exception as e:
        print('Task price summary is not ready yet.....') 
        print(e)
        return -1
    




def predict_best_node(task_name):
    w_net = 1 # Network profiling: longer time, higher price
    w_cpu = 100000 # Resource profiling : larger cpu resource, lower price
    w_mem = 100000 # Resource profiling : larger mem resource, lower price
    w_queue = 1 # Queue : currently 0
    best_node = -1
    task_price_network= dict()
    for (source, task), price in task_price_net.items():
        if task == task_name:
            task_price_network[source]= float(task_price_net[source,task])
    
    task_price_network[self_name] = 0 #the same node

    if len(task_price_network.keys())>1: #net(node,home) not exist
        task_price_summary = dict()
        
        for item, p in task_price_cpu.items():
            if item in home_ids: continue
            test = pass_time[item].__call__()
            if test==True: 
                task_price_network[item] = float('Inf')
            task_price_summary[item] = task_price_cpu[item]*w_cpu +  task_price_mem[item]*w_mem + task_price_queue[item]*w_queue + task_price_network[item]*w_net
        
        best_node = min(task_price_summary,key=task_price_summary.get)
    else:
        print('Task price summary is not ready yet.....') 
    return best_node


def announce_price(price):
    """Announce my current price to the task controller given its IP
    
    Args:
        task_controller_ip (str): IP of the task controllers
        price: my current price
    """
    # print('Announce my price')
    for node_id in combined_ip_map:
        if node_id == self_name: continue
        try:
            url = "http://" + combined_ip_map[node_id] + ":" + str(FLASK_SVC) + "/receive_price_info"
            pricing_info = self_name+"#"+str(price['cpu'])+"#"+str(price['memory'])+"#"+str(price['queue'])
            for task in price['network']:
                pricing_info = pricing_info + "$"+task+":"+price['network'][task]
            params = {'pricing_info':pricing_info}
            params = urllib.parse.urlencode(params)
            req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
            res = urllib.request.urlopen(req)
            res = res.read()
            res = res.decode('utf-8')

            if BOKEH==3:    
                topic = 'msgoverhead_%s'%(self_name)
                msg = 'msgoverhead priceintegrated compute%s updateprice 1\n'%(self_name)
                demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
        except Exception as e:
            print("Sending price message to flask server on other compute nodes FAILED!!!")
            print(e)
            return "not ok"

def push_updated_price():
    """Push my current price to all the task controllers
    """
    price = price_aggregate()
    announce_price(price)

    
def schedule_update_price(interval):
    """Schedule the price update procedure every interval
    
    Args:
        interval (int): chosen interval (minutes)
    """
    sched = BackgroundScheduler()
    sched.add_job(push_updated_price,'interval',id='push_price', minutes=interval, replace_existing=True)
    sched.start()

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

def announce_input_worker():
    try:
        print('Receive input announcement from the home node')
        tmp_file = request.args.get('input_file')
        tmp_time = request.args.get('input_time')
        tmp_info = request.args.get('home_id')
        tmp_home = tmp_info.split('-')[1]
        print('Current mapping list')
        print("Received input announcement from home compute")
        start_times[(tmp_home,tmp_file)] = tmp_time
        mapping_input_id[(tmp_home,tmp_file)] = len(mapping_times)-1 #ID of last mapping

    except Exception as e:
        print("Received mapping announcement from controller failed")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/announce_input_worker', 'announce_input_worker', announce_input_worker)


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
            if flag=='true': 
                print('not wait, send')
                runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
                send_runtime_profile_computingnode(runtime_info,task_name,home_id)

                destinations = ["/centralized_scheduler/input/" +x + "/"+home_id+"/"+new_file for x in next_tasks_map[task_name]]
                for idx,host in enumerate(next_hosts):
                    if self_ip!=combined_ip_map[host]: # different node
                        transfer_data(host,username,password,event.pathname, destinations[idx])
                    else: # same node
                        copyfile(event.pathname, destinations[idx])
            else:
                print('Wait until enough output files')
                if key not in files_mul:
                    files_mul[key] = [event.pathname]
                else:
                    files_mul[key] = files_mul[key] + [event.pathname]

                if len(files_mul[key]) == len(next_hosts):
                    # send runtime info on finishing the task 
                    print('Enough output files')
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
            size_mul[key] = cal_file_size(event.pathname)
            next_mul[key] = [task_flag]
        else:
            task_mul[key] = task_mul[key] + [new_file]
            count_mul[key]=count_mul[key]-1
            size_mul[key] = size_mul[key] + cal_file_size(event.pathname)

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

class Graph(): 
    def __init__(self,vertices): 
        self.graph = defaultdict(list) #dictionary containing adjacency List 
        self.V = vertices #List of vertices 
  
    # function to add an edge to graph 
    def addEdge(self,u,v): 
        self.graph[u].append(v) 
    def topologicalSort(self): 
              
        #in_degree = [0]*(self.V) 
        in_degree = dict.fromkeys(self.V, 0)
          
        # Traverse adjacency lists to fill indegrees of 
           # vertices.  This step takes O(V+E) time 
        for i in self.graph: 
            for j in self.graph[i]:
                in_degree[j] += 1

        # Create an queue and enqueue all vertices with 
        # indegree 0 
        queue = [] 
        # for i in range(self.V):
        for i in self.V:
            if in_degree[i] == 0:
                queue.append(i) 

        #Initialize count of visited vertices 
        cnt = 0

        # Create a vector to store result (A topological 
        # ordering of the vertices) 
        top_order = [] 

        # One by one dequeue vertices from queue and enqueue 
        # adjacents if indegree of adjacent becomes 0 
        while queue: 

            # Extract front of queue (or perform dequeue) 
            # and add it to topological order 
            u = queue.pop(0) 
            top_order.append(u) 
            # Iterate through all neighbouring nodes 
            # of dequeued node u and decrease their in-degree 
            # by 1 
            for i in self.graph[u]: 
                in_degree[i] -= 1
                # If in-degree becomes zero, add it to queue 
                if in_degree[i] == 0: 
                    queue.append(i)
            cnt += 1

        # Check if there was a cycle 
        if cnt != len(self.V): 
            print("There exists a cycle in the graph")
            return None
        else : 
            #Print topological order 
            print(top_order) 
            return top_order

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

    global BOKEH_SERVER, BOKEH_PORT, BOKEH, appname, appoption
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

    appname = os.environ['APPNAME']
    appoption = os.environ['APPOPTION']
    

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

    global sample_file, sample_size
    sample_file= '/centralized_scheduler/1botnet.ipsum'
    sample_size = cal_file_size(sample_file)
    

    web_server = MonitorRecv()
    web_server.start()

    # Update execution information file
    _thread.start_new_thread(update_exec_profile_file,())


    _thread.start_new_thread(schedule_update_price,(update_interval,))
    
    _thread.start_new_thread(schedule_update_assignment,(update_interval,))
    time.sleep(30)
    _thread.start_new_thread(schedule_update_global,(update_interval,))
    # Update pricing information every interval

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