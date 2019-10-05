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
# import pandas as pd
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import urllib
from apscheduler.schedulers.background import BackgroundScheduler
from readconfig import read_config
from shutil import copyfile
import paho.mqtt.client as mqtt

import pyinotify

app = Flask(__name__)

def tic():
    return time.time()

def toc(t):
    texec = time.time() - t
    # print('Execution time is:'+str(texec))
    return texec

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
    global self_profiler_ip,profiler_ip, profiler_nodes,exec_home_ip, self_name,self_ip, task_controllers, task_controllers_ips, home_ips,home_ids, home_ip_map
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
    

    task_controllers = os.environ['ALL_NODES'].split(':')
    task_controllers_ips = os.environ['ALL_NODES_IPS'].split(':')

    computing_nodes = os.environ['ALL_COMPUTING_NODES'].split(':')
    computing_ips = os.environ['ALL_COMPUTING_IPS'].split(':')

    global combined_ip_map
    combined_nodes = home_ids + computing_nodes
    combined_ips = home_ips + computing_ips
    combined_ip_map = dict(zip(combined_nodes,combined_ips))

    global manager,task_mul, count_mul, queue_mul, size_mul,next_mul, files_mul, controllers_id_map, task_node_map

    manager = Manager()
    task_mul = manager.dict() # list of incoming tasks and files
    count_mul = manager.dict() # number of input files required for each task
    queue_mul = manager.dict() # tasks which have not yet been processed
    size_mul  = manager.dict() # total input size of each incoming task and file
    next_mul = manager.dict() # information of next node (IP,username,pass) fo the current file
    files_mul = manager.dict()
    controllers_id_map = manager.dict()
    task_node_map = manager.dict()

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

    controllers_ip_map = dict(zip(task_controllers, task_controllers_ips))
    computing_ip_map = dict(zip(computing_nodes, computing_ips))
    
    for task in task_controllers:
        if task in super_tasks:
            computing_ip_map[task] = controllers_ip_map[task]

    # print(computing_ip_map)  

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
        task_node_map[home_id]  = home_id
        next_tasks_map[home_id] = [os.environ['CHILD_NODES']]
        last_tasks_map[os.environ['CHILD_NODES']].append(home_id)


    for task in task_controllers:
        # print(task)
        if task in super_tasks:
            task_node_map[task] = task    
    # print('DEBUG NEXT LAST-----------')
    # print(next_tasks_map)
    # print(last_tasks_map)
    # print(task_node_map)

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
    # print('@@@@@@@@@@@@@@@@@@@@@@@@')
    # print(name_convert_out)
    # print(name_convert_in)


    

    
    

    

    # CHECK NON_DAG tasks
    global configs, taskmap

    configs = json.load(open('/centralized_scheduler/config.json'))
    taskmap = configs["taskname_map"]
    execution_map = configs['exec_profiler']


    print('Generating task folders for OUTPUT\n')
    global task_module
    task_module = {}
    # print(taskmap)
    # print(execution_map)
    for task in dag:
        # print(task)
        # print(taskmap[task][1])
        if taskmap[task][1] and execution_map[task]: #DAG
            task_module[task] = __import__(task)
            cmd = "mkdir centralized_scheduler/output/"+task 
            os.system(cmd)
            for home_id in home_ids:
                cmd = "mkdir centralized_scheduler/output/"+task+"/" + home_id
                os.system(cmd)

    # print(task_module)
    print('Generating task folders for INPUT\n')
    for task in dag:
        if taskmap[task][1]: #DAG
            cmd = "mkdir centralized_scheduler/input/"+task 
            os.system(cmd)
            for home_id in home_ids:
                cmd = "mkdir centralized_scheduler/input/"+task+"/" + home_id
                os.system(cmd)

    # print(task_module)

    

def update_controller_map():
    """
        Update matching between task controllers and node, in case task controllers are crashed and redeployded
    """
    try:
        info = request.args.get('controller_id_map').split(':')
        # print("--- Received controller info")
        # print(info)
        #Task, Node
        controllers_id_map[info[0]] = info[1]

    except Exception as e:
        print("Bad reception or failed processing in Flask for controllers matching announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/update_controller_map', 'update_controller_map', update_controller_map)

def receive_assignment_info():
    """
        Receive corresponding best nodes from the corresponding computing node
    """
    try:
        print('Receive assignment information from task controllers')
        assignment_info = request.args.get('assignment_info').split('#')
        # print("Received assignment info")
        task_node_map[assignment_info[0]] = assignment_info[1]
        # print(task_node_map)
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

    # collection = db.collection_names(include_system_collections=False)
    # print('Collections in the database:')
    # for collect in collection:
    #     print(collect)


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
        # print(record)
        info_to_csv=[record['Task'],record['Duration [sec]'],str(record['Output File [Kbit]'])]
        execution_info.append(info_to_csv)
        c = c+1
    print('Execution information has already been provided')
    with open('execution_log.txt','w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(execution_info)
    if BOKEH==3:    
        topic = 'msgoverhead_%s'%(self_name)
        msg = 'msgoverhead pricepushcompute%s updateexec %d\n'%(self_name,c)
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
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
    print('Retrieve network information info')
    network_info = dict()        
    try:
        client_mongo = MongoClient('mongodb://'+self_profiler_ip+':'+str(MONGO_SVC)+'/')
        db = client_mongo.droplet_network_profiler
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
        print(collection)
        # print(num_nb)
        # print(self_profiler_ip)
        if num_nb == -1:
            print('--- Network profiler mongoDB not yet prepared')
            return network_info
        num_rows = db[self_profiler_ip].count() 
        print(num_rows)
        if num_rows < num_nb:
            print('--- Network profiler regression info not yet loaded into MongoDB!')
            return network_info
        # logging =db[self_profiler_ip].find().limit(num_nb)  
        logging =db[self_profiler_ip].find().skip(db[self_profiler_ip].count()-num_nb)
        print(logging)
        c = 0 
        for record in logging:
            # print(record)
            # print(ip_profilers_map)
            # print(record['Destination[IP]'])
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            network_info[ip_profilers_map[record['Destination[IP]']]] = str(record['Parameters'])
            c=c+1
        
        print('Checking BOKEH')
        print(BOKEH)
        if BOKEH==3:    
            topic = 'msgoverhead_%s'%(self_name)
            msg = 'msgoverhead pricepushcompute%s updatenetwork %d\n'%(self_name,c)
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
        print(len(resource_info))
        if BOKEH==3:    
            topic = 'msgoverhead_%s'%(self_name)
            msg = 'msgoverhead pricepushcompute%s updateresource %d\n'%(self_name,len(resource_info))
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
        return resource_info
    except Exception as e:
        print("Resource request failed. Will try again, details: " + str(e))
        return -1
        
# def get_updated_resource_profile():
#     """Requesting resource profiler data using flask for its corresponding profiler node
#     """
#     #print("----- Get updated resource profile information") 
#     resource_info = [] 
#     try:
#         for c in range(0,num_retries):

#             #print("http://" + self_profiler_ip + ":" + str(FLASK_SVC) + "/all")
#             r = requests.get("http://" + self_profiler_ip + ":" + str(FLASK_SVC) + "/all")
#             result = r.json()
#             if len(result) != 0:
#                 resource_info=result
#                 break
#             time.sleep(1)

#         if c == num_retries:
#             print("Exceeded maximum try times.")

#         # print("Resource profiles: ", resource_info)
#         print("Resource profiles: ", resource_info)
#         print(len(resource_info))
#         if BOKEH==3:    
#             topic = 'msgoverhead_%s'%(self_name)
#             msg = 'msgoverhead pricepushcompute%s updateresource %d\n'%(self_name,len(resource_info))
#             demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
#         return resource_info

#     except Exception as e:
#         print("Resource request failed. Will try again, details: " + str(e))
#         return -1

def price_aggregate(task_name):
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
        test_size = cal_file_size('/centralized_scheduler/1botnet.ipsum')
        
        
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
        test_output = execution_info[task_name][1]
        # print(test_output)

        price['network'] = dict()
        for node in network_info:
            # print('==')
            # print(node)
            # print(network_info[node])
            computing_params = network_info[node].split(' ')
            # print('====')
            # print(computing_params)
            computing_params = [float(x) for x in computing_params]
            # print(computing_params)
            p = (computing_params[0] * test_output * test_output) + (computing_params[1] * test_output) + computing_params[2]
            # print(p)
            # print(node)
            price['network'][node] = p
            
        # print(price['network'])
        # print('-----------------')
        print('Overall price:')
        print(price)
        return price
             
    except:
        print('Error reading input information to calculate the price')
        
    return price


def announce_price(task_controller_ip, price):
    """Announce my current price to the task controller given its IP
    
    Args:
        task_controller_ip (str): IP of the task controllers
        price: my current price
    """
    try:

        print("Announce my price")
        url = "http://" + task_controller_ip + ":" + str(FLASK_SVC) + "/receive_price_info"
        pricing_info = self_name+"#"+str(price['cpu'])+"#"+str(price['memory'])+"#"+str(price['queue'])
        for node in price['network']:
            # print(node)
            # print(price['network'][node])
            pricing_info = pricing_info + "$"+node+"%"+str(price['network'][node])
        
        # print(pricing_info)
        # print(url)
        # print(task_controller_ip)
        params = {'pricing_info':pricing_info}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending price message to flask server on controller node FAILED!!!")
        print(e)
        return "not ok"

def push_updated_price():
    """Push my current price to all the task controllers
    """
    # print('***********')
    # print(task_controllers)
    # print(controllers_ip_map)
    for idx,task in enumerate(task_controllers):
        if task in home_ids: continue
        if task in super_tasks: continue 
        if task in non_tasks: continue 
        price = price_aggregate(task)
        # print('Uhmmmm')
        # print(task)
        # print(controllers_ip_map)
        # print(controllers_ip_map[task])
        # print(price)
        announce_price(controllers_ip_map[task], price)

    
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
    
    def transfer_data_scp(ID,user,pword,source, destination):
        """Transfer data using SCP
        
        Args:
            ID (str): destination ID
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
        ID (str): destination ID 
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

class Handler1(pyinotify.ProcessEvent):
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
        runtime_info = 'rt_finish '+ input_name + ' '+str(ts)

        send_runtime_profile_computingnode(runtime_info,task_name,home_id)
        key = (home_id,task_name,input_name)

        flag = next_mul[key][0]

        if next_tasks_map[task_name][0] in home_ids: 
            # print('----- next step is home')
            transfer_data(home_id,username,password,event.pathname, "/output/"+new_file)   
        else:
            # print('----- next step is not home')
            print(task_node_map)
            print(len(profiler_nodes))
            while len(task_node_map)<len(profiler_nodes):
                print('Not yet loaded assignment')
                print(task_node_map)
                time.sleep(1)
            next_hosts =  [task_node_map[x] for x in next_tasks_map[task_name]]
            # next_IPs   = [computing_ip_map[x] for x in next_hosts]

            # print('Sending the output files to the corresponding destinations')
            if flag=='true': 
                #send a single output of the task to all its children 
                destinations = ["/centralized_scheduler/input/" +x + "/"+home_id+"/"+new_file for x in next_tasks_map[task_name]]
                for idx,host in enumerate(next_hosts):
                    if self_ip!=combined_ip_map[host]: # different node
                        transfer_data(host,username,password,event.pathname, destinations[idx])
                    else: # same node
                        copyfile(event.pathname, destinations[idx])
            else:
                #it will wait the output files and start putting them into queue, send frst output to first listed child, ....
                if key not in files_mul:
                    files_mul[key] = [event.pathname]
                else:
                    files_mul[key] = files_mul[key] + [event.pathname]
                if len(files_mul[key]) == len(next_hosts):
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
        """On every node, whenever there is scheduling information sent from the central network profiler:
            - Connect the database
            - Scheduling measurement procedure
            - Scheduling regression procedure
            - Start the schedulers
        
        Args:
            event (ProcessEvent): a new file is created
        """

        print("Received file as input - %s." % event.pathname)

        new_file = os.path.split(event.pathname)[-1]
        if '_' in new_file:
            file_name = new_file.split('_')[0]
        else:
            file_name = new_file.split('.')[0]

        ts = time.time()
        # task_name = new_file.split('#')[2]
        # home_id = new_file.split('#')[1]
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
            # print('--------------Add task to the processing queue')
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

    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

    update_interval = 3

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
    # Update pricing information every interval

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
    eh1 = Handler1()
    notifier1= pyinotify.Notifier(wm1, eh1)
    notifier1.loop()

    
    

if __name__ == '__main__':
    main()