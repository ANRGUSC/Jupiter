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
import numpy as np
from collections import defaultdict
from shutil import copyfile
import paho.mqtt.client as mqtt

app = Flask(__name__)

global bottleneck
bottleneck = defaultdict(list)


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

    global manager,task_mul, count_mul, queue_mul, size_mul,next_mul, files_mul, controllers_id_map, task_node_map, update_best,task_node_summary

    manager = Manager()
    task_mul = manager.dict() # list of incoming tasks and files
    count_mul = manager.dict() # number of input files required for each task
    queue_mul = manager.dict() # tasks which have not yet been processed
    size_mul  = manager.dict() # total input size of each incoming task and file
    next_mul = manager.dict() # information of next node (IP,username,pass) fo the current file
    files_mul = manager.dict()
    controllers_id_map = manager.dict()
    task_node_map = manager.dict()
    update_best = manager.dict()
    # task_node_summary = manager.dict()

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

    global next_tasks_map,last_tasks_map
    next_tasks_map = dict()
    last_tasks_map = dict()

    # CHECK NON_DAG tasks
    global configs, taskmap

    configs = json.load(open('/centralized_scheduler/config.json'))
    taskmap = configs["taskname_map"]
    execution_map = configs['exec_profiler']

    
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
        # task_node_map[home_id]  = home_id
        next_tasks_map[home_id] = [os.environ['CHILD_NODES']]
        last_tasks_map[os.environ['CHILD_NODES']].append(home_id)

    # for task in task_controllers:
    #     print(task)
    #     if task in super_tasks:
    #         task_node_map[task] = task    
    # print('DEBUG NEXT LAST-----------')
    # print(next_tasks_map)
    # print(last_tasks_map)
    # print(task_node_map)

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
        # print('***************************************************')
        # print('update controller map')
        # t = tic()
        info = request.args.get('controller_id_map').split('#')
        # print("--- Received controller info")
        # print(info)
        #Task, Node
        controllers_id_map[info[0]] = info[1]
        # txec = toc(t)
        # bottleneck['updatecontroller'].append(txec)
        # print(np.mean(bottleneck['updatecontroller']))
        # print('***************************************************')

    except Exception as e:
        print("Bad reception or failed processing in Flask for controllers matching announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/update_controller_map', 'update_controller_map', update_controller_map)


def update_exec_profile_file():
    """Update the execution profile from the home execution profiler's MongoDB and store it in text file.
    """
    # print('***************************************************')
    # print('Retrieve execution information info')
    # t = tic()
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


    c = 0
    for record in logging:
        # Node ID, Task, Execution Time, Output size
        info_to_csv=[record['Task'],record['Duration [sec]'],str(record['Output File [Kbit]'])]
        execution_info.append(info_to_csv)
        c+=1
    print('Execution information has already been provided')
    with open('execution_log.txt','w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(execution_info)

    if BOKEH==5:    
        topic = 'msgoverhead_%s'%(self_name)
        msg = 'msgoverhead priceeventcompute%s updateexec %d\n'%(self_name,c)
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    # txec = toc(t)
    # bottleneck['executioninfo'].append(txec)
    # print(np.mean(bottleneck['executioninfo']))
    # print('***************************************************')
    return


def get_updated_execution_profile():
    """Get updated execution information from the generated text file
    """
    # print('***************************************************')
    # print('----- Get updated execution information')
    # t = tic()

    with open('execution_log.txt','r') as f:
        reader = csv.reader(f)
        execution = list(reader)
    
    execution_info = {}
    for row in execution:
        execution_info[row[0]] = [float(row[1]),float(row[2])]
    # txec = toc(t)
    # bottleneck['readexec'].append(txec)
    # print(np.mean(bottleneck['readexec']))
    # print('***************************************************')
    return execution_info

def get_updated_network_profile():
    """
        Get updated network information from the network profilers
    """
   
    print('Retrieve network information info')
    network_info = dict()        
    try:
        # print('***************************************************')
        # t = tic()
        client_mongo = MongoClient('mongodb://'+self_profiler_ip+':'+str(MONGO_SVC)+'/')
        db = client_mongo.droplet_network_profiler
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
        # print(collection)
        # print(num_nb)
        # print(self_profiler_ip)
        if num_nb == -1:
            print('--- Network profiler mongoDB not yet prepared')
            return network_info
        num_rows = db[self_profiler_ip].count() 
        # print(num_rows)
        if num_rows < num_nb:
            print('--- Network profiler regression info not yet loaded into MongoDB!')
            return network_info
        # logging =db[self_profiler_ip].find().limit(num_nb)
        logging =db[self_profiler_ip].find().skip(db[self_profiler_ip].count()-num_nb)  
        # print(logging)
        c = 0
        for record in logging:
            # print(record)
            # print(ip_profilers_map)
            # print(record['Destination[IP]'])
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            network_info[ip_profilers_map[record['Destination[IP]']]] = str(record['Parameters'])
            c+=1
        # txec = toc(t)
        # bottleneck['netinfo'].append(txec)
        # print(np.mean(bottleneck['netinfo']))
        # print('***************************************************')

        if BOKEH==5:    
            topic = 'msgoverhead_%s'%(self_name)
            msg = 'msgoverhead priceeventcompute%s updatenetwork %d\n'%(self_name,c)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
        return network_info
    except Exception as e:
        print("Network request failed. Will try again, details: " + str(e))
        return -1

def get_updated_resource_profile():
    """Requesting resource profiler data using flask for its corresponding profiler node
    """

    print("----- Get updated resource profile information") 
    resource_info = [] 
    try:
        # print('***************************************************')
        # t = tic()
        for c in range(0,num_retries):
            t1 = time.time()
            #print("http://" + self_profiler_ip + ":" + str(FLASK_SVC) + "/all")
            r = requests.get("http://" + self_profiler_ip + ":" + str(FLASK_SVC) + "/all")
            result = r.json()
            if len(result) != 0:
                resource_info=result
                break
            time.sleep(1)
            # print(time.time()-t1)

        if c == num_retries:
            print("Exceeded maximum try times.")
        # txec = toc(t)
        # bottleneck['resourceinfo'].append(txec)
        # print(np.mean(bottleneck['resourceinfo']))
        # print('***************************************************')
        print("Resource profiles: ", resource_info)
        print(len(resource_info))
        if BOKEH==5:    
            topic = 'msgoverhead_%s'%(self_name)
            msg = 'msgoverhead priceeventcompute%s updateresource %d\n'%(self_name,len(resource_info))
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
        return resource_info

    except Exception as e:
        print("Resource request failed. Will try again, details: " + str(e))
        return -1

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
        # print('***************************************************')
        print(' Retrieve all input information: ')
        # t = tic()
        execution_info = get_updated_execution_profile()
        resource_info = get_updated_resource_profile()
        # print(resource_info)
        network_info = get_updated_network_profile()
        # print(network_info)
        test_size = cal_file_size('/centralized_scheduler/1botnet.ipsum')
        
        
        # print('----- Calculating price:')
        # print('--- Resource cost: ')
        price['memory'] = float(resource_info[self_name]["memory"])
        price['cpu'] = float(resource_info[self_name]["cpu"])
        # print(price['memory'])
        # print(price['cpu'])

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
        # print(execution_info)
        # print(task_name)
        # print(execution_info[task_name])
        test_output = execution_info[task_name][1]
        # print(test_output)
        # print(network_info)
        # print(type(network_info))
        price['network'] = dict()
        for node in network_info:
            # print(network_info[node])
            computing_params = network_info[node].split(' ')
            # print(computing_params)
            computing_params = [float(x) for x in computing_params]
            # print(computing_params)
            p = (computing_params[0] * test_output * test_output) + (computing_params[1] * test_output) + computing_params[2]
            # print(p)
            # print(node)
            price['network'][node] = p
            
        # print(price['network'])
        # print('-----------------')
        # print('Overall price:')
        # print(price)
        # txec = toc(t)
        # bottleneck['priceagg'].append(txec)
        # print(np.mean(bottleneck['priceagg']))
        # print('***************************************************')
        return price
             
    except:
        print('Error reading input information to calculate the price')
        
    return price


def announce_price(task_controller_ip, price):
    """
        Announce my current price (network, resource, task queue) to the corresponding task controller 

        Args:
            task_controller_ip (str): IP of the task controller
            price: my current price
    """
    try:
        # print('***************************************************')
        # print("Announce my price")
        # t = tic()
        # t1=time.time()
        url = "http://" + task_controller_ip + ":" + str(FLASK_SVC) + "/receive_price_info"
        pricing_info = self_name+"#"+str(price['cpu'])+"#"+str(price['memory'])+"#"+str(price['queue'])
        # print(time.time()-t1)
        # t1 = time.time()
        for node in price['network']:
            # print(node)
            # print(price['network'][node])
            pricing_info = pricing_info + "$"+node+"%"+str(price['network'][node])
        # print(time.time()-t1)
        # print(pricing_info)
        # t1 = time.time()
        params = {'pricing_info':pricing_info}
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
        res = res.decode('utf-8')
        # print(time.time()-t1)
        # txec = toc(t)
        # bottleneck['announceprice'].append(txec)
        # print(np.mean(bottleneck['announceprice']))
        # print('***************************************************')
    except Exception as e:
        print("Sending price message to flask server on controller node FAILED!!!")
        print(e)
        return "not ok"

def push_updated_price():
    """Push the update price to all the task controllers
    """
    # print('Update price')
    # print(task_controllers)
    # print(home_ids)
    for idx,task in enumerate(task_controllers):
        if task in home_ids: continue
        if task in super_tasks: continue 
        if task in non_tasks: continue 
        price = price_aggregate(task)
        # print(price)
        announce_price(controllers_ip_map[task], price)

    if BOKEH==5:    
        topic = 'msgoverhead_%s'%(self_name)
        msg = 'msgoverhead priceeventcompute%s pushprice %d\n'%(self_name,len(task_controllers))

    
def schedule_update_price(interval):
    """Schedule the price update procedure every given interval
    
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
    # print('***************************************************')
    # print('Execute task')
    # t = tic()
    ts = time.time()
    runtime_info = 'rt_exec '+ file_name+ ' '+str(ts)
    send_runtime_profile_computingnode(runtime_info,task_name,home_id)
    dag_task = multiprocessing.Process(target=task_module[task_name].task, args=(filenames, input_path, output_path))
    dag_task.start()
    dag_task.join()
    # txec = toc(t)
    # bottleneck['exectask'].append(txec)
    # print(np.mean(bottleneck['exectask']))
    # print('***************************************************')
    
    
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
        # print('***************************************************')
        # print('Transfer data SCP')
        # print(IP)
        # print(user)
        # print(pword)
        # print(source)
        # print(destination)
        # t = tic()
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
        # txec = toc(t)
        # bottleneck['transfer'].append(txec)
        # print(np.mean(bottleneck['transfer']))
        # print('***************************************************')

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
        task_name (str): task name
        home_id (str): id of the home
    
    Returns:
        str: the message if successful, "not ok" otherwise.
    
    No Longer Raises:
        Exception: if sending message to flask server on home is failed
    """
    try:
        # print('***************************************************')
        # print("Sending message", msg)
        # t = tic()
        # t1 = time.time()
        url = "http://" + home_node_host_ports[home_id] + "/recv_runtime_profile_computingnode"
        params = {'msg': msg, "work_node": self_name, "task_name": task_name}
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
        res = res.decode('utf-8')
        # print(time.time()-t1)
        # t1 = time.time()
        # txec = toc(t)
        # bottleneck['sendmsg'].append(txec)
        # # print(np.mean(bottleneck['sendmsg']))
        # print('***************************************************')
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
    # bottleneck['retrieveinput'].append(txec)
    # print(np.mean(bottleneck['retrieveinput']))
    # sprint('***************************************************')
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

def request_best_assignment(home_id,task_name,file_name):
    """Request the best computing node for the task
    
    Args:
        home_id (str): id of the home
        task_name (str): name of the current task
        file_name (str): name of the current processed file
        original_task (str): name of the previous task
    
    """
    try:
        # print('***************************************************')
        # print("Request the best computing node for the task" + task_name)
        # t = tic()
        url = "http://" + controllers_ip_map[task_name] + ":" + str(FLASK_SVC) + "/receive_best_assignment_request"
        params = {'home_id':home_id,'node_name':self_name,'file_name':file_name,'key':self_name}
        # print(params)
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')

        if BOKEH==5:    
            topic = 'msgoverhead_%s'%(self_name)
            msg = 'msgoverhead priceeventcompute%s requestbest 1\n'%(self_name)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)


        # txec = toc(t)
        # bottleneck['reequestassign'].append(txec)
        # print(np.mean(bottleneck['requestassign']))
        # print('***************************************************')
    except Exception as e:
        print("Sending assignment request to flask server on controller node FAILED!!!")
        print(e)
        return "not ok"

def receive_best_assignment():
    """
        Receive the best computing node for the task
    """
    
    try:
        # print('***************************************************')
        # print("Received best assignment")
        # t = tic()
        home_id = request.args.get('home_id')
        task_name = request.args.get('task_name')
        file_name = request.args.get('file_name')
        best_computing_node = request.args.get('best_computing_node')
        task_node_map[home_id,task_name,file_name] = best_computing_node
        # task_node_summary[home_id,task_name,file_name] = best_computing_node
        # print(task_name)
        # print(best_computing_node)
        # print(task_node_summary)
        update_best[home_id,task_name,file_name] = True
        # txec = toc(t)
        # bottleneck['receiveassign'].append(txec)
        # print(np.mean(bottleneck['receiveassign']))
        # print('***************************************************')

    except Exception as e:
        update_best[home_id,task_name,file_name] = False
        print("Bad reception or failed processing in Flask for best assignment request: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_best_assignment', 'receive_best_assignment', receive_best_assignment)

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
             
            # print('***************************************************')
            print("Received file as output - %s." % event.src_path)
            # t = tic()

            # t1 = time.time()
            new_file = os.path.split(event.src_path)[-1]

            if '_' in new_file:
                temp_name = new_file.split('_')[0]
            else:
                temp_name = new_file.split('.')[0]

            
            ts = time.time()
            
            # print(time.time()-t1)
            # t1 = time.time()
            if RUNTIME == 1:
                s = "{:<10} {:<10} {:<10} {:<10} \n".format(self_name,transfer_type,event.src_path,ts)
                runtime_receiver_log.write(s)
                runtime_receiver_log.flush()

            task_name = event.src_path.split('/')[-3]
            home_id = event.src_path.split('/')[-2]
            # print(task_name)
            # print(home_id)
            input_name = retrieve_input_finish(task_name, temp_name)
            # print('????????????????')
            # print(input_name)
            runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
            # print(time.time()-t1)
            # t1 = time.time()
            send_runtime_profile_computingnode(runtime_info,task_name,home_id)
            # print(time.time()-t1)
            # t1 = time.time()
            key = (home_id,task_name,input_name)
            # print('#############')
            # print(next_mul)
            flag = next_mul[key][0]
            # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            # print(new_file)
            # print(next_tasks_map)
            # print(next_tasks_map[task_name])
            # print(flag)
            # print(time.time()-t1)
            # t1 = time.time()
            if next_tasks_map[task_name][0] in home_ids: # next node is HOME
                print('----- next step is home')
                transfer_data(home_ip_map[home_id],username,password,event.src_path, "/output/"+new_file)   
                # print(time.time()-t1)
                # t1 = time.time() 
            else: #next node is another compute node
                # print('----- next step is not home')
                # print(next_tasks_map[task_name])
                # print(len(next_tasks_map[task_name]))
                # print('Sending the output files to the corresponding destinations')
                
                for next_task in next_tasks_map[task_name]:
                    # print(next_task)
                    # print(super_tasks)
                    # print(non_tasks)
                    # print(next_task in super_tasks)      
                    # print(next_task in non_tasks)  
                    # print(next_task in super_tasks or non_tasks)
                    if next_task in super_tasks or next_task in non_tasks: 
                        print('next task is non DAG')
                        continue
                    while not update_best[home_id,next_task,input_name]:
                        request_best_assignment(home_id,next_task,input_name)
                        print('--- waiting for computing node assignment')
                        time.sleep(1)
                # print(time.time()-t1)
                # t1 = time.time()
                # print('---------- Now what')
                # print(computing_ip_map)
                # print(task_node_map)

                next_hosts = []
                next_IPs = []

                # print('--------------------')
                for next_task in next_tasks_map[task_name]:
                    # print(next_task)
                    if next_task in super_tasks or next_task in non_tasks: 
                        # print('next task is non DAG')
                        next_hosts.append(next_task)
                        next_IPs.append(controllers_ip_map[next_task])
                    else:
                        tmp_host = task_node_map[home_id,next_task,input_name]
                        # print('next task is DAGssss')
                        # print(tmp_host)
                        next_hosts.append(tmp_host)  
                        next_IPs.append(computing_ip_map[tmp_host]) 


                # print(task_node_map[home_id,next_task,input_name])
                # # print(task_node_summary[home_id,next_task,input_name])
                # next_hosts =  [task_node_map[home_id,x,input_name] for x in next_tasks_map[task_name]]
                # # next_hosts =  [task_node_summary[home_id,x,input_name] for x in next_tasks_map[task_name]]
                # next_IPs   = [computing_ip_map[x] for x in next_hosts]

                # print('**************!!!!!!!!!!!!!!!!!!!!!')
                # print(next_tasks_map[task_name])
                # print(flag)

                if flag=='true': # same output to all of the children task
                    # print(flag)
                    # print(type(flag))
                    # print('same output to all of the children task')
                    destinations = ["/centralized_scheduler/input/" +x + "/"+home_id+"/"+new_file for x in next_tasks_map[task_name]]
                    # destinations = ["/centralized_scheduler/input/" +new_file+"#"+home_id +"#"+x for x in next_tasks_map[task_name]]
                    #destinations = ["/centralized_scheduler/input/" +x + "/"+home_id+"/"+new_file for x in next_tasks_map[task_name]]
                    # print(destinations)
                    for idx,ip in enumerate(next_IPs):
                        # print('----')
                        # print(ip)
                        # print(destinations[idx])
                        if self_ip!=ip:
                            # print('different')
                            # print(event.src_path)
                            # print(destinations[idx])
                            transfer_data(ip,username,password,event.src_path, destinations[idx])
                        else:
                            # cmd = "cp %s %s"%(event.src_path,destinations[idx])
                            # print(cmd)
                            # os.system(cmd)
                            # print('same')
                            # print(event.src_path)
                            # print(destinations[idx])
                            copyfile(event.src_path, destinations[idx])
                    # print(time.time()-t1)
                    # t1 = time.time()
                else: #each output file to each of the next children task
                    # print('each output file to each of the next children task')
                    if key not in files_mul:
                        files_mul[key] = [event.src_path]
                    else:
                        files_mul[key] = files_mul[key] + [event.src_path]
                    # print(files_mul[key])
                    # print(time.time()-t1)
                    # t1 = time.time()

                    if len(files_mul[key]) == len(next_IPs):
                        for idx,ip in enumerate(next_IPs):
                            # print(files_mul[key][idx])
                            # print(next_tasks_map[task_name][idx])
                            current_file = files_mul[key][idx].split('/')[-1]
                            # print(current_file)
                            # destinations = "/centralized_scheduler/input/" +current_file +"#"+home_id+"#"+next_tasks_map[task_name][idx]
                            destinations = "/centralized_scheduler/input/" +next_tasks_map[task_name][idx]+"/"+home_id+"/"+current_file
                            #destinations = "/centralized_scheduler/input/" +next_tasks_map[task_name][idx]+"/"+home_id
                            # print(destinations)
                            if self_ip!=ip:
                                # print('different')
                                # print(files_mul[key][idx])
                                transfer_data(ip,username,password,files_mul[key][idx], destinations)
                            else: 
                                # cmd = "cp %s %s"%(files_mul[key][idx],destinations)
                                # # print(cmd)
                                # os.system(cmd)
                                # print('same')
                                # print(files_mul[key][idx])
                                copyfile(files_mul[key][idx],destinations)
                    # print(time.time()-t1)
             
            # txec = toc(t)
            # bottleneck['receiveoutput'].append(txec)
            # # print(np.mean(bottleneck['receiveoutput']))
            # print('***************************************************')

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

            # print('***************************************************')
            print("Received file as input - %s." % event.src_path)
            # t = tic()

            # t1 = time.time()
            new_file = os.path.split(event.src_path)[-1]
            if '_' in new_file:
                file_name = new_file.split('_')[0]
            else:
                file_name = new_file.split('.')[0]

            ts = time.time()
            # print(time.time()-t1)
            # t1 = time.time()
            # print('***************************************^^^^^^^^^^^')
            
            # print(file_name)
            # home_id = new_file.split('#')[1]
            # task_name = new_file.split('#')[2]
            # print(new_file)
            # print(event.src_path.split('/'))
            home_id = event.src_path.split('/')[-2]
            task_name = event.src_path.split('/')[-3]
            # print(home_id)
            # print(task_name)
            input_name = retrieve_input_enter(task_name, file_name)
            # print('???????????')
            # print(input_name)
            runtime_info = 'rt_enter '+ input_name + ' '+str(ts)
            key = (home_id,task_name,input_name)
            # print(time.time()-t1)
            # t1 = time.time()
            send_runtime_profile_computingnode(runtime_info,task_name,home_id)
            # print(time.time()-t1)
            # t1 = time.time()
            # print(next_tasks_map)
            # print(next_tasks_map[task_name])
            for next_task in next_tasks_map[task_name]:
                update_best[home_id,next_task,input_name]= False
            flag = dag[task_name][0] 
            task_flag = dag[task_name][1] 
            # print('&&&&&&&&&&&&&&&&&&&&')
            # print(dag[task_name])
            # print(flag)
            # print(time.time()-t1)
            # t1 = time.time()

            if key not in task_mul:
                task_mul[key] = [new_file]
                count_mul[key]= int(flag)-1
                size_mul[key] = cal_file_size(event.src_path)
                next_mul[key] = [task_flag]
                # print(time.time()-t1)
                # t1 = time.time()
            else:
                task_mul[key] = task_mul[key] + [new_file]
                count_mul[key]=count_mul[key]-1
                size_mul[key] = size_mul[key] + cal_file_size(event.src_path)
                # print(time.time()-t1)
                # t1 = time.time()

            if count_mul[key] == 0: # enough input files
                incoming_file = task_mul[key]
                if len(incoming_file)==1: 
                    filenames = incoming_file[0]
                else:
                    filenames = incoming_file
                # print(time.time()-t1)
                # t1 = time.time()
                # print('Add task to the processing queue')
                queue_mul[key] = False 
                

                input_path = os.path.split(event.src_path)[0]
                output_path = input_path.replace("input","output")
                # output_path = os.path.join(os.path.split(input_path)[0],'output')
                #output_path = os.path.join(output_path,task_name,home_id)

                # print(output_path)
                # print(time.time()-t1)
                # t1 = time.time()
                # print('!!!!!!!!!')
                # print(input_name)
                execute_task(home_id,task_name,input_name, filenames, input_path, output_path)
                # print(time.time()-t1)
                queue_mul[key] = True
            # txec = toc(t)
            # bottleneck['receiveinput'].append(txec)
            # # print(np.mean(bottleneck['receiveinput']))
            # print('***************************************************')
                

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
    global runtime_sender_log, RUNTIME, TRANSFER, transfer_type, node_ip_map
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

    #monitor INPUT as another process
    w=Watcher()
    w.start()

    #monitor OUTPUT in this process
    w1=Watcher1()
    w1.run()

    
    

if __name__ == '__main__':
    main()