#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on every computing node of the system.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
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
import pandas as pd
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import urllib.request
from urllib import parse


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
    for line in tasks_info:
        if count == 0:
            count += 1
            continue

        data = line.strip().split(" ")
        if task_map[data[0]][1] == True and execution_map[data[0]] == False:
            if data[0] not in super_tasks:
                super_tasks.append(data[0])
        if task_map[data[0]][1] == False:
            continue

        tasks.setdefault(data[0], [])
        if data[0] not in task_order:
            task_order.append(data[0])
        for i in range(3, len(data)):
            if  data[i] != 'home' and task_map[data[i]][1] == True :
                tasks[data[0]].append(data[i])
    # print("tasks: ", tasks)
    # print("task order", task_order) #task_list
    # print("super tasks", super_tasks)
    return tasks, task_order, super_tasks

def prepare_global_info():
    """Get information of corresponding profiler (network profiler, execution profiler)"""
    global self_profiler_ip,profiler_ip, profiler_nodes,exec_home_ip, self_name,self_ip,ip_node_map,node_ip_map
    profiler_ip = os.environ['ALL_PROFILERS'].split(' ')
    profiler_ip = [info.split(":") for info in profiler_ip]

    profiler_nodes = os.environ['ALL_PROFILERS_NODES'].split(' ')
    profiler_nodes = [info.split(":") for info in profiler_nodes]
   
    self_profiler_ip = os.environ['PROFILERS']
    exec_home_ip = os.environ['EXECUTION_HOME_IP']
    self_name = os.environ['NODE_NAME']
    self_ip = os.environ['SELF_IP']

    ip_node_map = dict(zip(profiler_ip[0], profiler_nodes[0]))
    node_ip_map = dict(zip(profiler_nodes[0], profiler_ip[0]))

    global manager,task_mul, count_mul, queue_mul, size_mul,task_to_ip

    manager = Manager()
    task_mul = manager.dict() # list of incoming tasks and files
    count_mul = manager.dict() # number of input files required for each task
    queue_mul = manager.dict() # tasks which have not yet been processed
    size_mul  = manager.dict() # total input size of each incoming task and file
    task_to_ip = manager.dict()

    global home_node_host_port, dag
    home_node_host_port = os.environ['HOME_NODE'] + ":" + str(FLASK_SVC)

    dag_file = '/centralized_scheduler/dag.txt'
    dag_info = k8s_read_dag(dag_file)
    dag = dag_info[1]
    
    global task_module
    # print('Task modules')
    # print(dag)
    # print(dag.keys())
    task_module = {}
    for task in dag:
        print(task)
        task_module[task] = __import__(task)
        cmd = "mkdir centralized_scheduler/output/" + task 
        os.system(cmd)
    # print(task_module)


def update_exec_profile_file():
    """Update the execution profile from the home execution profiler's MongoDB and store it in text file.
    """
    # print('Update execution profile information in execution.txt')
    # print(exec_home_ip)
    # print(MONGO_SVC)

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
            time.sleep(60)

    while not available_data:
        try:
            logging =db[self_name].find()
            available_data = True
        except:
            print('Execution information for the current node is not ready!!!')
            time.sleep(60)

    for record in logging:
        # Node ID, Task, Execution Time, Output size
        info_to_csv=[record['Task'],record['Duration [sec]'],str(record['Output File [Kbit]'])]
        execution_info.append(info_to_csv)
    print('Execution information has already been provided')
    # print(execution_info)
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
    #print(execution_info)
    return execution_info

def get_updated_network_from_source(node_ip):
    #print("--- Get updated network profile information from "+node_ip)   
    network_info = {}
    try:
        #print('mongodb://'+node_ip+':'+str(MONGO_SVC)+'/')
        client_mongo = MongoClient('mongodb://'+node_ip+':'+str(MONGO_SVC)+'/')
        db = client_mongo.droplet_network_profiler
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
        if num_nb == -1:
            print('--- Network profiler mongoDB not yet prepared')
            return network_info
        num_rows = db[node_ip].count() 
        if num_rows < num_nb:
            print('--- Network profiler regression info not yet loaded into MongoDB!')
            return network_info
        logging =db[node_ip].find().limit(num_nb)  
        for record in logging:
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            # info_to_csv=[ip_node_map[record['Source[IP]']],record['Source[IP]'],ip_node_map[record['Destination[IP]']], record['Destination[IP]'],str(record['Parameters'])]
            network_info[ip_node_map[record['Destination[IP]']]] = str(record['Parameters'])
        #print("Network information from the source node: ", network_info)
        return network_info
    except Exception as e:
        print("Network request failed. Will try again, details: " + str(e))
        return -1

def get_updated_network_profile(node_name):
    """Collect the network profile information from local MONGODB database
    
    Args:
        node_name (str): the source node of the requesting task
    
    Returns:
        list: network information
    """
    #print('----- Get updated network information:')
    computing_net_info = get_updated_network_from_source(self_profiler_ip)
    # print(node_ip_map)
    # print(node_name)
    task_profiler_ip = node_ip_map[node_name]
    # print(task_profiler_ip)
    controller_net_info = get_updated_network_from_source(task_profiler_ip)
    return computing_net_info,controller_net_info

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
            time.sleep(60)

        if c == num_retries:
            print("Exceeded maximum try times.")

        # print("Resource profiles: ", resource_info)
        return resource_info

    except Exception as e:
        print("Resource request failed. Will try again, details: " + str(e))
        return -1

def pricing_calculate(file_name, task_name, task_ip,node_name,file_size):
    """Calculate price required to perform the task with given input based on network information, resource information, execution information and task queue size
    
    Args:
        file_name (str): incoming file name
        task_name (str): incoming task name
        file_size (str): incoming file size
    
    Returns:
        float: calculated price
    """

    # Default values
    price = 100000
    w_net = 1 # Network
    w_cpu = 1 # Resource
    w_mem = 1 # Resource
    w_queue = 1 # Execution time

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
        computing_net_info,controller_net_info = get_updated_network_profile(node_name)
        # print('--- Resource: ')
        # print(resource_info)
        # print('--- Network: ')
        # print(computing_net_info)
        # print(controller_net_info)
        # print('--- Execution: ')
        # print(execution_info)
        test_execution_size = cal_file_size('/centralized_scheduler/1botnet.ipsum')
        # print('----Task queue: ')
        # print(queue_mul)
        print('----- Calculating price:')
        print('--- Resource cost: ')
        mem_cost = float(resource_info[self_name]["memory"])
        cpu_cost = float(resource_info[self_name]["cpu"])
        print(mem_cost)
        print(cpu_cost)
        print('--- Network cost: ')
        # print(node_name)
        if node_name in computing_net_info.keys():
            computing_params = computing_net_info[node_name].split()
            controller_params = controller_net_info[self_name].split()
            computing_params = [float(x) for x in computing_params]
            controller_params = [float(x) for x in controller_params]
            # print(computing_params)
            # print(controller_params)
            estimated_output = execution_info[task_name][1]* test_execution_size / file_size
            # print(estimated_output)
            network_cost = (controller_params[0] * file_size * file_size) + \
                           (controller_params[1] * file_size) + \
                           controller_params[2] + \
                           (computing_params[0] * estimated_output * estimated_output) + \
                           (computing_params[1] * estimated_output) + \
                           computing_params[2]
        else:
            network_cost = 0 
        print(network_cost)
        #Temporary: linear
        print('--- Queuing cost: ')
        print(task_queue_size)

        if task_queue_size == -1: #infinite tasks
            queue_cost = 0
        else:
            if len(queue_mul)==0:
                queue_cost = 0
                print('empty queue, no tasks are waiting')
            else:
                queue_dict = dict(queue_mul)
                queue_task = [k for k,v in queue_dict.items() if v == False]
                size_dict = dict(size_mul)
                queue_size =  [size_dict[k] for k in queue_dict.keys()]
                queue_cost = 0 
                # print(queue_task)
                # print(queue_size)
                for idx,task_info in enumerate(queue_task):
                    #TO_DO: sum or max
                    queue_cost = queue_cost + execution_info[task_info[0]][0]* queue_size[idx] / test_execution_size 
        #print(queue_cost)

        price = w_net * network_cost + w_cpu * cpu_cost + w_mem * mem_cost + \
                w_queue * queue_cost

        print('--- Final price: ')
        print(price)
        return price
             
    except:
        print('Error reading input information to calculate the price')
        
    return price

def announce_price(task_controller_ip, file_name, price):
    try:

        print("Announce my price")
        url = "http://" + task_controller_ip + ":" + str(FLASK_SVC) + "/receive_price_info"
        pricing_info = file_name+"#"+self_name+"#"+self_ip+"#"+str(price)
        params = {'pricing_info':pricing_info}
        #params = {'file_name':file_name , "node_name": self_name, "node_ip":self_ip, "price": price}
        params = parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending message to flask server on controller node FAILED!!!")
        print(e)
        return "not ok"

def receive_price_request():
    """Receive price request from pricing calculator
    """
    price = 0
    try:
        file_name = request.args.get('file_name')
        file_size = float(request.args.get('file_size'))
        task_name = request.args.get('task_name')
        task_ip   = request.args.get('task_ip')
        node_name = request.args.get('node_name')
        print('---------------------------------')
        print("Received pricing request message:", task_name, file_size,file_name,node_name)
        price = pricing_calculate(file_name, task_name, task_ip,node_name,file_size)
        # print('Estimated price for the current request')
        # print(price)
        # print(task_ip)
        announce_price(task_ip, file_name, price)

    except Exception as e:
        print("Bad reception or failed processing in Flask for pricing request: "+ e)
        return "not ok"
    return "ok"
app.add_url_rule('/receive_price_request', 'receive_price_request', receive_price_request)

# def send_runtime_profile(msg,task_name):
#     """
#     Sending runtime profiling information to flask server on home

#     Args:
#         msg (str): the message to be sent

#     Returns:
#         str: the message if successful, "not ok" otherwise.

#     Raises:
#         Exception: if sending message to flask server on home is failed
#     """
#     try:
#         print("Sending message", msg)
#         url = "http://" + home_node_host_port + "/recv_runtime_profile"
#         params = {'msg': msg, "work_node": task_name}
#         params = parse.urlencode(params)
#         req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
#         res = urllib.request.urlopen(req)
#         res = res.read()
#         res = res.decode('utf-8')
#     except Exception as e:
#         print("Sending runtime profiling info to flask server on home FAILED!!!")
#         print(e)
#         return "not ok"
#     return res

def execute_task(task_name,file_name, filenames, input_path, output_path):
    """Execute the task given the input information
    
    Args:
        task_name (str): incoming task name
        filenames (str): incoming files
        input_path (str): input file path
        output_path (str): output file path
    """
    dag_task = multiprocessing.Process(target=task_module[task_name].task, args=(filenames, input_path, output_path))
    dag_task.start()
    dag_task.join()
    
    

def transfer_data_scp(IP,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        IP (str): destination IP address
        user (str): username
        pword (str): password
        source (str): source file path
        destination (str): destination file path
    """
    retry = 0
    while retry < num_retries:
        try:
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, IP, destination)
            os.system(cmd)
            # print('data transfer complete\n')
            break
        except:
            print('Task controller: SSH Connection refused or File transfer failed, will retry in 2 seconds')
            time.sleep(2)
        retry += 1

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
                time.sleep(5)
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
        global task_to_ip
        if event.is_directory:
            return None

        elif event.event_type == 'created':
             
            print("Received file as output - %s." % event.src_path)
            task_name = event.src_path.split('/')[-2]
            # print(task_name)
            # print(task_to_ip)
            task_ip = task_to_ip[task_name]
            # print(task_ip)
            transfer_data_scp(task_ip,username,password,event.src_path, "/centralized_scheduler/output/")

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
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()

class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        global task_to_ip

        if event.is_directory:
            return None

        elif event.event_type == 'created':

            print("Received file as input - %s." % event.src_path)

            new_file = os.path.split(event.src_path)[-1]
            if '_' in new_file:
                file_name = new_file.split('_')[0]
            else:
                file_name = new_file.split('.')[0]
            
            task_name = new_file.split('#')[1]
            task_ip = new_file.split('#')[2]
            if task_name not in task_to_ip: 
                task_to_ip[task_name] = task_ip
    
            key = (task_name,file_name)
            flag = dag[task_name][0] 
            if key not in task_mul:
                task_mul[key] = [new_file]
                count_mul[key]= int(flag)-1
                size_mul[key] = cal_file_size(event.src_path)
            else:
                task_mul[key] = task_mul[key] + [new_file]
                count_mul[key]=count_mul[key]-1
                size_mul[key] = size_mul[key] + cal_file_size(event.src_path)
            
            # print('Incoming files:')
            
            # print(task_mul)
            # print(count_mul)
            # print(size_mul)

            if count_mul[key] == 0: # enough input files
                incoming_file = task_mul[key]
                if len(incoming_file)==1: 
                    filenames = incoming_file[0]
                else:
                    filenames = incoming_file
                print('Add task to the processing queue')
                queue_mul[key] = False 
                # print(queue_mul)

                input_path = os.path.split(event.src_path)[0]
                output_path = os.path.join(os.path.split(input_path)[0],'output')
                # print(output_path)
                output_path = os.path.join(output_path,task_name)
                # print(output_path)

                execute_task(task_name,file_name, filenames, input_path, output_path)
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
    ## Load all the configuration
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


    prepare_global_info()

    web_server = MonitorRecv()
    web_server.start()

    _thread.start_new_thread(update_exec_profile_file,())

    #monitor INPUT as another process
    w=Watcher()
    w.start()

    #monitor OUTPUT in this process
    w1=Watcher1()
    w1.run()
    

if __name__ == '__main__':
    main()