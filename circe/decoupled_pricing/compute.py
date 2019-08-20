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

app = Flask(__name__)

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
    # task_controllers = os.environ['ALL_NODES'].split(':')
    # task_controllers_ips = os.environ['ALL_NODES_IPS'].split(':')
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
    # print('--------- CHECK')
    for home_id in home_ids:
        # print(home_id)
        home_node_host_ports[home_id] = home_ip_map[home_id] + ":" + str(FLASK_SVC)
        # print(home_node_host_ports)

    dag_file = '/centralized_scheduler/dag.txt'
    dag_info = k8s_read_dag(dag_file)
    dag = dag_info[1]


    global tasks, task_order, super_tasks, non_tasks
    tasks, task_order, super_tasks, non_tasks = get_taskmap()
    print('----------- TASKS INFO')
    print(tasks)
    print(task_order)
    print(super_tasks)
    print(non_tasks)

    # for task in tasks:
    #     my_task_price_net[task] = dict()    


    global ip_profilers_map,profilers_ip_map, controllers_ip_map, computing_ip_map, profilers_ip_homes
    # print('DEBUG')
    # print(profiler_nodes)
    # print(profiler_ip)
    
    ip_profilers_map = dict(zip(profiler_ip, profiler_nodes))
    profilers_ip_map = dict(zip(profiler_nodes, profiler_ip))

    # print(home_nodes)
    # print(home_ids)
    # print(home_ips)
    # print(profilers_ip_map)
    # print(ip_profilers_map)
    profilers_ip_homes = [profilers_ip_map[x] for x in home_ids]

    # controllers_ip_map = dict(zip(task_controllers, task_controllers_ips))
    computing_ip_map = dict(zip(computing_nodes, computing_ips))
    
    # for task in task_controllers:
    #     if task in super_tasks:
    #         computing_ip_map[task] = controllers_ip_map[task]




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
    print('Graph')
    print(top_order_task)

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

    # print(task_module)

    
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
        # print(assignment_info)
        params = {'assignment_info': assignment_info}
        params = urllib.parse.urlencode(params)
        # print(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        # print(req)
        res = urllib.request.urlopen(req)
        # print(res)
        res = res.read()
        # print(res)
        res = res.decode('utf-8')
    except Exception as e:
        print("The computing node is not yet available. Sending assignment message to flask server on computing node FAILED!!!")
        print(e)
        # print(node_ip)
        # print(self_name)
        # print(task_name)
        # print(best_node)
        return "not ok"

def push_assignment_map():
    """Update assignment periodically
    """
    print('Updated assignment periodically')
    for task in tasks:
        # print('*********************************************')
        # print('update compute nodes')
        # print(all_computing_nodes)
        # print(task)

        best_node = predict_best_node(task)
        # print(best_node)
        # print('----')
        # print(self_name)
        local_task_node_map[self_name,task] = best_node
    # print('===================================')
    # print(local_task_node_map)
    # for computing_ip in computing_ips:
    task_list = ''
    best_list = ''
    t0 = 0
    for task in tasks:
        # print(task)
        # print(local_task_node_map[self_name,task])
        if local_task_node_map[self_name,task]==-1:
            print('Best node has not been provided yet')
            break
        task_list = task_list+':'+task
        best_list = best_list+':'+local_task_node_map[self_name,task]
        t0 = t0+1
    task_list = task_list[1:]
    best_list = best_list[1:]
    
    if t0 == len(tasks):
        for computing_ip in combined_ips:
            # print(computing_ip)
            send_assignment_info(computing_ip,task_list,best_list)
    else:
        print('Not yet assignment!')
        # print('*********************************************')
        # print('home nodes')
        # print(home_ips)
        # print(home_ids)
        # for home_ip in home_ips:
            # send_assignment_info(home_ip)
        # print('*********************************************')
        # print('controller non_dag')
        # print(controller_nondag)
        # for controller_ip in controller_ip_nondag:
        #     send_assignment_info(controller_ip)
        # announce_best_assignment_to_child()
    # else:
    #     print('Current best computing node not yet assigned!')

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
    m = (len(computing_nodes)+1)*len(tasks) # (all_compute & home,all_task)
    a = dict(local_task_node_map)
    if len(a)<m:
        print('Not yet fully loaded local information')
    else: 
        print('Fully loaded information')
        for home in home_ids:
            for task in top_order_task:
                # print('--------------')
                # print(task)
                # print(global_task_node_map)
                # print(last_tasks_map[task])
                if task==first_task:
                    global_task_node_map[home,first_task]=local_task_node_map[home,first_task]
                else:
                    if len(last_tasks_map[task])==1:
                        prev_node = global_task_node_map[home,last_tasks_map[task][0]]
                        global_task_node_map[home,task] = local_task_node_map[prev_node,task]
                    else:
                        tmp_node_list =[]
                        for prev_task in last_tasks_map[task]:
                            prev_node = global_task_node_map[home,prev_task]
                        last_tasks_map[task].sort()
                        # print(last_tasks_map[task])
                        chosen_task = last_tasks_map[task][0]
                        chosen_prev = global_task_node_map[home,chosen_task]
                        # print(chosen_task)
                        # print(chosen_prev)
                        global_task_node_map[home,task] = local_task_node_map[chosen_prev,task]

        print(global_task_node_map)

def receive_assignment_info():
    """
        Receive corresponding best nodes from the corresponding computing node
    """
    try:
        # print('Receive assignment info')
        assignment_info = request.args.get('assignment_info').split('#')
        # print("Received assignment info")
        task_list = assignment_info[1].split(':')
        best_list = assignment_info[2].split(':')
        for task in task_list:
            for best_node in best_list:
                local_task_node_map[assignment_info[0],task] = best_node
        # print(local_task_node_map)
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

    for record in logging:
        # Node ID, Task, Execution Time, Output size
        # print(record)
        info_to_csv=[record['Task'],record['Duration [sec]'],str(record['Output File [Kbit]'])]
        execution_info.append(info_to_csv)
    print('Execution information has already been provided')
    with open('execution_log.txt','w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(execution_info)
    return


def get_updated_execution_profile():
    """Get updated execution information from text file
    """
    #print('----- Get updated execution information')

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
    #print('Retrieve network information info')
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
        logging =db[self_profiler_ip].find().limit(num_nb)  
        for record in logging:
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            network_info[ip_profilers_map[record['Destination[IP]']]] = str(record['Parameters'])
        
        return network_info
    except Exception as e:
        print("Network request failed. Will try again, details: " + str(e))
        return -1
        
def get_updated_resource_profile():
    """Requesting resource profiler data using flask for its corresponding profiler node
    """
    #print("----- Get updated resource profile information") 
    resource_info = [] 
    try:
        for c in range(0,num_retries):

            #print("http://" + self_profiler_ip + ":" + str(FLASK_SVC) + "/all")
            r = requests.get("http://" + self_profiler_ip + ":" + str(FLASK_SVC) + "/all")
            result = r.json()
            if len(result) != 0:
                resource_info=result
                break
            time.sleep(1)

        if c == num_retries:
            print("Exceeded maximum try times.")

        # print("Resource profiles: ", resource_info)
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
    # print(sys.maxsize)

    """
    Input information:
        - Resource information: resource_info
        - Network information: network_info
        - Task queue: task_mul
        - Execution information: execution_info
    """

    try:
        
        #print(' Retrieve all input information: ')
        execution_info = get_updated_execution_profile()
        resource_info = get_updated_resource_profile()
        # print('--------------')
        # print(resource_info)
        # print('--------------2')
        # print(execution_info)
        network_info = get_updated_network_profile()
        # print('--------------3')
        # print(network_info)
        # test_size = cal_file_size('/centralized_scheduler/1botnet.ipsum')
        
        
        # print('----- Calculating price:')
        # print('--- Resource cost: ')
        price['memory'] = float(resource_info[self_name]["memory"])
        price['cpu'] = float(resource_info[self_name]["cpu"])

        # print('--- Queuing cost: ')
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
        # print(price['queue'])

        # print('--- Network cost:----------- ')
        # print(task_name)

        price['network'] = dict()
        # print(tasks)
        # print(network_info)
        
        for task in tasks:
            # print(task)
            if task in home_ids: continue
            if task in super_tasks: continue 
            if task in non_tasks: continue 
            test_output = execution_info[task][1]
            # print(test_output)
            tmp_price = sys.maxsize
            tmp_node = -1
            for node in network_info:
                # print(test_output)
                # print('==')
                # print(node)
                # print(network_info[node])
                computing_params = network_info[node].split(' ')
                # print('====')
                # print(computing_params)
                computing_params = [float(x) for x in computing_params]
                # print(computing_params)
                p = (computing_params[0] * test_output * test_output) + (computing_params[1] * test_output) + computing_params[2]
                # print('update my network price')
                # print(node)
                # print(p)
                my_task_price_net[(task,node)] = p
                if p < tmp_price:
                    tmp_price = p
                    tmp_node = node
            # print('---')
            # print(tmp_price)
            # print(tmp_node)
            price['network'][task] = str(tmp_price)
            # local_task_node_map[task] = tmp_node #next best compute for a specific task on my node #network only
        # print(price['network'])


            
        
        print('-----------------')
        print('Overall price:')
        # print(local_task_node_map)
        # print(price['network'])
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
        # print("Received pricing info")
        # print(pricing_info)
        #Network, CPU, Memory, Queue
        node_name = pricing_info[0]

        task_price_cpu[node_name] = float(pricing_info[1])
        task_price_mem[node_name] = float(pricing_info[2])
        task_price_queue[node_name] = float(pricing_info[3].split('$')[0])
        price_net_info = pricing_info[3].split('$')[1:]
        for price in price_net_info:
            task_price_net[node_name,price.split(':')[0]] = float(price.split(':')[1])

        # print('Check price updated interval ')
        pass_time[node_name] = TimedValue()


    except Exception as e:
        print("Bad reception or failed processing in Flask for pricing announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_price_info', 'receive_price_info', receive_price_info) 


def predict_best_node(task_name):
    # print('***************************************************')
    # print('Select the current best node')
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
    # # print(len(task_price_net))
    # # print(source_node)
    # # print('DEBUG')

    # # I am the source node
    # # print(my_task)
    # print('--------5')
    # print(self_name)
    # print(next_task)
    # print(task_price_net.keys())
    # from next node 
    for (source, task), price in task_price_net.items():
        # print('***')
        # print(source)
        if task == task_name:
            # print('hehehehe')
            # print(source)
            # print(dest)
            # print(task_price_net[source,dest])
            task_price_network[source]= float(task_price_net[source,task])

    
    # print('uhmmmmmmm')
    
    task_price_network[self_name] = 0 #the same node

    # print('price of home node')
    
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
    # print(my_task_price_net.keys())
    # print(my_task_price_net)
    # print(task_price_cpu.items())
    if len(task_price_network.keys())>1: #net(node,home) not exist
        #print('------------2')
        task_price_summary = dict()
        
        for item, p in task_price_cpu.items():
            # print('---')
            # print(item)
            # print(p)
            if item in home_ids: continue
            # print(task_price_cpu[item])
            # print(task_price_mem[item])
            # print(task_price_queue[item])
            # print(task_price_network[item])

            # check time pass
            # print('Check passing time------------------')
            # print(pass_time.keys())
            test = pass_time[item].__call__()
            # print(test)
            if test==True: 
                # print('Yeahhhhhhhhhhhhhhhhhhhhhh')
                task_price_network[item] = float('Inf')
            # print(task_price_network[item])
            
            # print(task_price_cpu[item])
            # print(task_price_queue[item])
            # print(task_price_mem[item])
            # print(task_price_network[item])
            task_price_summary[item] = task_price_cpu[item]*w_cpu +  task_price_mem[item]*w_mem + task_price_queue[item]*w_queue + task_price_network[item]*w_net
            # print(task_price_summary[item])
        
        # print('Summary cost')
        # print(task_price_summary)
        best_node = min(task_price_summary,key=task_price_summary.get)
        # print('Best node for '+task_name)
        # print(best_node)

        # txec = toc(t)
        # bottleneck['selectbest'].append(txec)
        # print(np.mean(bottleneck['selectbest']))
        # print('***************************************************')
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
        # print('------------')
        # print(node_id)
        # print(self_name)

        if node_id == self_name: continue
        try:
            # print('------------2')
            # print("Announce my price")
            url = "http://" + combined_ip_map[node_id] + ":" + str(FLASK_SVC) + "/receive_price_info"
            pricing_info = self_name+"#"+str(price['cpu'])+"#"+str(price['memory'])+"#"+str(price['queue'])
            # print(pricing_info)
            # print('===')
            # print(price['network'])
            for task in price['network']:
                # print(task)
                # print(price['network'][task])
                pricing_info = pricing_info + "$"+task+":"+price['network'][task]
            # print('====1')
            # print(pricing_info)
            # print('-------------4')
            # print(url)
            # print(task_controller_ip)
            params = {'pricing_info':pricing_info}
            params = urllib.parse.urlencode(params)
            # print('-------------5')
            # print(url)
            # print(params)
            req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
            res = urllib.request.urlopen(req)
            # print('-------------6')
            res = res.read()
            res = res.decode('utf-8')
            # print('------------3')
        except Exception as e:
            print("Sending price message to flask server on other compute nodes FAILED!!!")
            # print(node_id)
            print(e)
            return "not ok"

def push_updated_price():
    """Push my current price to all the task controllers
    """
    # print('***********')
    # print(task_controllers)
    # print(controllers_ip_map)
    # for idx,task in enumerate(task_controllers):

    # for task in tasks:
    #     if task in home_ids: continue
    #     if task in super_tasks: continue 
    #     if task in non_tasks: continue 
    price = price_aggregate()
    # print('-----------------')
    # print('Uhmmmm')
    # print(task)
    # print(controllers_ip_map)
    # print(controllers_ip_map[task])
    # print(price)
    # print(task)
    # print(price)
    announce_price(price)

    
def schedule_update_price(interval):
    """Schedule the price update procedure every interval
    
    Args:
        interval (int): chosen interval (minutes)
    """
    # scheduling updated price
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
    # print('*** Perform the task!!!')
    # print(task_name)
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
    
    def transfer_data_scp(IP,user,pword,source, destination):
        """Transfer data using SCP
        
        Args:
            IP (str): destination IP address
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
                cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, IP, destination)
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
    # print('***************************************************')
    # print('retrieve input name')
    # t = tic()
    # t1 = time.time()
    # print(file_name)
    # print(task_name)
    # print(name_convert_in)
    suffix = name_convert_in[task_name]
    # print(suffix)
    # print(time.time()-t1)
    # t1 = time.time()
    # print(suffix)
    # print(type(suffix))
    prefix = file_name.split(suffix)
    # print(prefix)
    # print(time.time()-t1)
    # t1 = time.time()
    # print('$$$$$$')
    # print(file_name)
    # print(suffix)
    # print(prefix)
    input_name = prefix[0]+name_convert_in['input']
    # print(time.time()-t1)
    # print(input_name)
    # txec = toc(t)
    # #bottleneck['retrieveinput'].append(txec)
    # # print(np.mean(bottleneck['retrieveinput']))
    # print('***************************************************')
    return input_name

def retrieve_input_finish(task_name, file_name):
    """Retrieve the corresponding input name based on the name conversion provided by the user and the output file name 
    
    Args:
        task_name (str): task name
        file_name (str): name of the file output at the OUTPUT folder
    """
    # print('***************************************************')
    # print('retrieve finish name')
    # print(file_name)
    # print(name_convert_out)
    suffix = name_convert_out[task_name]
    # print(suffix)
    prefix = file_name.split(suffix)
    # print('$$$$$$')
    # print(file_name)
    # print(suffix)
    # print(prefix)
    input_name = prefix[0]+name_convert_in['input']
    # print(input_name)
    # print('***************************************************')
    return input_name

#for OUTPUT folder 
class Watcher1():
    
    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'output/')

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.observer = Observer()

    def run(self):
        """
            Continuously watching the ``OUTPUT`` folder, if there is a new file created for the current task, copy the file to the corresponding ``INPUT`` folder of the next task in the scheduled node
        """
        event_handler = Handler1()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()

class Handler1(FileSystemEventHandler):


    @staticmethod
    def on_any_event(event):
        """
            Check for any event in the ``OUTPUT`` folder
        """
        if event.is_directory:
            return None

        elif event.event_type == 'created':
             
            print("Received file as output - %s." % event.src_path)


            new_file = os.path.split(event.src_path)[-1]

            if '_' in new_file:
                temp_name = new_file.split('_')[0]
            else:
                temp_name = new_file.split('.')[0]

            
            ts = time.time()
            
            if RUNTIME == 1:
                s = "{:<10} {:<10} {:<10} {:<10} \n".format(self_name,transfer_type,event.src_path,ts)
                runtime_receiver_log.write(s)
                runtime_receiver_log.flush()

            # print(event.src_path.split('#'))
            task_name = event.src_path.split('/')[-3]
            home_id = event.src_path.split('/')[-2]
            input_name = retrieve_input_finish(task_name, temp_name)
            # print('!!!!!!!!!!!!!!!!!------------------')
            # print(home_id)
            # print(task_name)

            # input_name = retrieve_input_finish(task_name, temp_name)
            # runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
            # # print(input_name)
            # send_runtime_profile_computingnode(runtime_info,task_name,home_id)

            key = (home_id,task_name,input_name)
            # print('#############')
            # print(next_mul)
            # print(key)
            flag = next_mul[key][0]
            # print(next_tasks_map)
            # print(next_tasks_map[task_name])
            # print(flag)
            # print('#############')
            # print(next_mul)
            #flag = next_mul[key][0]
            # print(next_tasks_map)
            # print(next_tasks_map[task_name])
            # print(flag)

            # print(next_tasks_map)
            # print(next_tasks_map[task_name])
            # print(next_tasks_map[task_name][0])
            if next_tasks_map[task_name][0] in home_ids: 
                print('----- next step is home')
                #send runtime info
                
                runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
                # print(input_name)
                send_runtime_profile_computingnode(runtime_info,task_name,home_id)
                transfer_data(home_ip_map[home_id],username,password,event.src_path, "/output/"+new_file)   
            else:
                print('----- next step is not home')
                # print(task_node_map)
                next_hosts = [global_task_node_map[home_id,x] for x in next_tasks_map[task_name]]
                # print(next_hosts)
                # print(global_task_node_map)
                # print('-----')
                # next_hosts =  [task_node_map[x] for x in next_tasks_map[task_name]]
                next_IPs   = [computing_ip_map[x] for x in next_hosts]
                
                # print(next_hosts)
                # print(next_IPs)
                
                # print(next_tasks_map[task_name])
                # print(flag)

                # print('Sending the output files to the corresponding destinations')
                if flag=='true': 
                    print('not wait, send')
                    # send runtime info
                    runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
                    # print(input_name)
                    send_runtime_profile_computingnode(runtime_info,task_name,home_id)

                    #send a single output of the task to all its children 
                    destinations = ["/centralized_scheduler/input/" +x + "/"+home_id+"/"+new_file for x in next_tasks_map[task_name]]
                    #destinations = ["/centralized_scheduler/input/" +new_file +"#"+home_id +"#"+x for x in next_tasks_map[task_name]]
                    for idx,ip in enumerate(next_IPs):
                        # print('----')
                        # print(ip)
                        # print(destinations[idx])
                        if self_ip!=ip: # different node
                            transfer_data(ip,username,password,event.src_path, destinations[idx])
                        else: # same node
                            # cmd = "cp %s %s"%(event.src_path,destinations[idx])
                            # print(cmd)
                            # os.system(cmd)
                            copyfile(event.src_path, destinations[idx])
                else:
                    #it will wait the output files and start putting them into queue, send frst output to first listed child, ....
                    print('wait')
                    if key not in files_mul:
                        files_mul[key] = [event.src_path]
                    else:
                        files_mul[key] = files_mul[key] + [event.src_path]
                    # print('-------------')
                    # print(files_mul[key])
                    # print(next_IPs)
                    # print(self_name)
                    # print(self_ip)
                    if len(files_mul[key]) == len(next_IPs):
                        # send runtime info on finishing the task 
                        runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
                        # print(input_name)
                        send_runtime_profile_computingnode(runtime_info,task_name,home_id)

                        for idx,ip in enumerate(next_IPs):
                            # print(files_mul[key][idx])
                            # print(next_tasks_map[task_name][idx])
                            current_file = files_mul[key][idx].split('/')[-1]
                            # print(current_file)
                            # destinations = "/centralized_scheduler/input/" +current_file +"#"+home_id+"#"+next_tasks_map[task_name][idx]
                            destinations = "/centralized_scheduler/input/" +next_tasks_map[task_name][idx]+"/"+home_id+"/"+current_file
                            # print(destinations)
                            if self_ip!=ip:
                                transfer_data(ip,username,password,files_mul[key][idx], destinations)
                            else: 
                                # cmd = "cp %s %s"%(files_mul[key][idx],destinations)
                                # # print(cmd)
                                # os.system(cmd)
                                copyfile(files_mul[key][idx],destinations)


#for INPUT folder
class Watcher(multiprocessing.Process):

    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'input/')
    
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.observer = Observer()

    def run(self):
        """
            Continuously watching the ``INPUT`` folder.
            When file in the input folder is received, based on the DAG info imported previously, it either waits for more input files, or issue pricing request to all the computing nodes in the system.
        """
        
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()

class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        

        if event.is_directory:
            return None

        elif event.event_type == 'created':

            print("Received file as input - %s." % event.src_path)

            new_file = os.path.split(event.src_path)[-1]
            if '_' in new_file:
                file_name = new_file.split('_')[0]
            else:
                file_name = new_file.split('.')[0]

            ts = time.time()
            # task_name = new_file.split('#')[2]
            # home_id = new_file.split('#')[1]
            home_id = event.src_path.split('/')[-2]
            task_name = event.src_path.split('/')[-3]
            
            input_name = retrieve_input_enter(task_name, file_name)
            runtime_info = 'rt_enter '+ input_name + ' '+str(ts)
            key = (home_id,task_name,input_name)
            send_runtime_profile_computingnode(runtime_info,task_name,home_id)

    
            
            flag = dag[task_name][0] 
            task_flag = dag[task_name][1] 
            # print('&&&&&&&&&&&&&&&&&&&&')
            # print(dag[task_name])
            # print(flag)
            # print(key)
            # print(task_mul)

            if key not in task_mul:
                task_mul[key] = [new_file]
                count_mul[key]= int(flag)-1
                size_mul[key] = cal_file_size(event.src_path)
                next_mul[key] = [task_flag]
            else:
                task_mul[key] = task_mul[key] + [new_file]
                count_mul[key]=count_mul[key]-1
                size_mul[key] = size_mul[key] + cal_file_size(event.src_path)

            # print('^^^^^^^^^^^^^^^')
            # print(count_mul[key])
            if count_mul[key] == 0: # enough input files
                incoming_file = task_mul[key]
                # print('^^^^^^^^^^^^^2')
                # print(incoming_file)
                if len(incoming_file)==1: 
                    filenames = incoming_file[0]
                else:
                    filenames = incoming_file
                # print(filenames)
                # print('--------------Add task to the processing queue')
                queue_mul[key] = False 
                
                input_path = os.path.split(event.src_path)[0]
                output_path = input_path.replace("input","output")
                
                # print('!!!!!!!!!')
                # print(input_name)
                # print(input_path)
                # print(output_path)
                # print(home_id)
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

    global first_task
    first_task  = 'task0' #fix later

    update_interval = 2

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

    # Update execution information file
    _thread.start_new_thread(update_exec_profile_file,())


    _thread.start_new_thread(schedule_update_price,(update_interval,))
    _thread.start_new_thread(schedule_update_assignment,(update_interval,))
    time.sleep(30)
    _thread.start_new_thread(schedule_update_global,(update_interval,))
    # Update pricing information every interval

    #monitor INPUT as another process
    w=Watcher()
    w.start()

    #monitor OUTPUT in this process
    w1=Watcher1()
    w1.run()

    
    

if __name__ == '__main__':
    main()