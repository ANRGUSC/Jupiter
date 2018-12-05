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
from apscheduler.schedulers.background import BackgroundScheduler
from readconfig import read_config

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
    return tasks, task_order, super_tasks

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


    global ip_profilers_map,profilers_ip_map, controllers_ip_map, computing_ip_map, profilers_ip_homes
    print('DEBUG')
    print(profiler_nodes)
    print(profiler_ip)
    

    ip_profilers_map = dict(zip(profiler_ip, profiler_nodes))
    profilers_ip_map = dict(zip(profiler_nodes, profiler_ip))

    print(home_nodes)
    print(home_ids)
    print(home_ips)
    print(profilers_ip_map)
    print(ip_profilers_map)
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
    print('@@@@@@@@@@@@@@@@@@@@@@@@')
    print(name_convert_out)
    print(name_convert_in)

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
    

    global home_node_host_port, dag
    home_node_host_ports = [x+ ":" + str(FLASK_SVC) for x in home_ips]

    dag_file = '/centralized_scheduler/dag.txt'
    dag_info = k8s_read_dag(dag_file)
    dag = dag_info[1]

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

    print('DEBUG NEXT LAST-----------')
    print(next_tasks_map)
    print(last_tasks_map)
    print(task_node_map)
    global task_module
    task_module = {}
    for home_id in home_ids:
        cmd = "mkdir centralized_scheduler/output/"+home_id
        os.system(cmd)
        for task in dag:
            task_module[task] = __import__(task)
            cmd = "mkdir centralized_scheduler/output/"+home_id+"/" + task 
            os.system(cmd)

def update_controller_map():
    """
        Update matching between task controllers and node, in case task controllers are crashed and redeployded
    """
    try:
        info = request.args.get('controller_id_map').split(':')
        print("--- Received controller info")
        print(info)
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
        assignment_info = request.args.get('assignment_info').split('#')
        print("Received assignment info")
        task_node_map[assignment_info[0]] = assignment_info[1]
        print(task_node_map)
    except Exception as e:
        print("Bad reception or failed processing in Flask for assignment announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_assignment_info', 'receive_assignment_info', receive_assignment_info)

def update_exec_profile_file():
    """Update the execution profile from the home execution profiler's MongoDB and store it in text file.
    """
    #print('Retrieve execution information info')
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
    
    #print('Retrieve network information info')
    network_info = dict()        
    try:
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
        logging =db[self_profiler_ip].find().limit(num_nb)  
        # print(logging)
        for record in logging:
            # print(record)
            # print(ip_profilers_map)
            # print(record['Destination[IP]'])
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
            time.sleep(60)

        if c == num_retries:
            print("Exceeded maximum try times.")

        # print("Resource profiles: ", resource_info)
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
    print(sys.maxsize)

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
        print(resource_info)
        network_info = get_updated_network_profile()
        print(network_info)
        test_size = cal_file_size('/centralized_scheduler/1botnet.ipsum')
        
        
        print('----- Calculating price:')
        print('--- Resource cost: ')
        price['memory'] = float(resource_info[self_name]["memory"])
        price['cpu'] = float(resource_info[self_name]["cpu"])
        print(price['memory'])
        print(price['cpu'])

        print('--- Queuing cost: ')
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
        print(price['queue'])

        print('--- Network cost:----------- ')
        test_output = execution_info[task_name][1]
        print(test_output)
        print(network_info)
        print(type(network_info))
        price['network'] = dict()
        for node in network_info:
            print(network_info[node])
            computing_params = network_info[node].split(' ')
            print(computing_params)
            computing_params = [float(x) for x in computing_params]
            print(computing_params)
            p = (computing_params[0] * test_output * test_output) + (computing_params[1] * test_output) + computing_params[2]
            print(p)
            print(node)
            price['network'][node] = p
            
        print(price['network'])
        print('-----------------')
        print('Overall price:')
        print(price)
        return price
             
    except:
        print('Error reading input information to calculate the price')
        
    return price


def announce_price(task_controller_ip, price):
    try:

        print("Announce my price")
        url = "http://" + task_controller_ip + ":" + str(FLASK_SVC) + "/receive_price_info"
        pricing_info = self_name+"#"+str(price['cpu'])+"#"+str(price['memory'])+"#"+str(price['queue'])
        for node in price['network']:
            print(node)
            print(price['network'][node])
            pricing_info = pricing_info + "$"+node+"-"+str(price['network'][node])
        
        print(pricing_info)
        params = {'pricing_info':pricing_info}
        params = parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending price message to flask server on controller node FAILED!!!")
        print(e)
        return "not ok"

def push_updated_price():
    # print('***********')
    # print(task_controllers)
    # print(controllers_ip_map)
    for idx,task in enumerate(task_controllers):
        if task in home_ids: continue
        price = price_aggregate(task)
        announce_price(controllers_ip_map[task], price)

    
def schedule_update_price(interval):
    # scheduling updated price
    sched = BackgroundScheduler()
    sched.add_job(push_updated_price,'interval',id='push_price', minutes=interval, replace_existing=True)
    sched.start()

def execute_task(task_name,file_name, filenames, input_path, output_path):
    """Execute the task given the input information
    
    Args:
        task_name (str): incoming task name
        filenames (str): incoming files
        input_path (str): input file path
        output_path (str): output file path
    """
    ts = time.time()
    runtime_info = 'rt_exec '+ file_name+ ' '+str(ts)
    send_runtime_profile_computingnode(runtime_info,task_name)
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
                time.sleep(2)
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

def send_runtime_profile_computingnode(msg,task_name):
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
        url = "http://" + home_node_host_port + "/recv_runtime_profile_computingnode"
        params = {'msg': msg, "work_node": self_name, "task_name": task_name}
        params = parse.urlencode(params)
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
    """Retrieve the corresponding input name based on the name conversion provided by the user and the output file name 
    
    Args:
        task_name (str): task name
        file_name (str): name of the file enter at the INPUT folder
    """
    suffix = name_convert_in[task_name]
    print(suffix)
    print(type(suffix))
    prefix = file_name.split(suffix)
    print('$$$$$$')
    print(file_name)
    print(suffix)
    print(prefix)
    input_name = prefix[0]+name_convert_in['input']
    print(input_name)
    return input_name

def retrieve_input_finish(task_name, file_name):
    """Retrieve the corresponding input name based on the name conversion provided by the user and the output file name 
    
    Args:
        task_name (str): task name
        file_name (str): name of the file output at the OUTPUT folder
    """
    suffix = name_convert_out[task_name]
    prefix = file_name.split(suffix)
    print('$$$$$$')
    print(file_name)
    print(suffix)
    print(prefix)
    input_name = prefix[0]+name_convert_in['input']
    print(input_name)
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

            task_name = event.src_path.split('/')[-2]
            home_id = event.src_path.split('/')[-3]
            print('!!!!!!!!!!!!!!!!!')
            print(home_id)
            print(task_name)
            input_name = retrieve_input_finish(task_name, temp_name)
            runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
            print(input_name)
            send_runtime_profile_computingnode(runtime_info,task_name)
            key = (task_name,input_name)
            print('#############')
            print(next_mul)
            flag = next_mul[key][0]
            print(next_tasks_map)
            print(next_tasks_map[task_name])
            print(flag)

            if next_tasks_map[task_name][0] in home_ids: 
                transfer_data(home_ip_map[home_id],username,password,event.src_path, "/output/"+new_file)    
            else: 
                next_hosts =  [task_node_map[x] for x in next_tasks_map[task_name]]
                next_IPs   = [computing_ip_map[x] for x in next_hosts]

                
                
                print('**************')
                print(next_hosts)
                print(next_IPs)
                print(next_tasks_map[task_name])
                print(flag)

                if flag == 'true':
                    destinations = ["/centralized_scheduler/input/" +new_file +"#"+x for x in next_tasks_map[task_name]]
                    for idx,ip in enumerate(next_IPs):
                        print('----')
                        print(ip)
                        print(destinations[idx])
                        if self_ip!=ip:
                            transfer_data(ip,username,password,event.src_path, destinations[idx])
                        else:
                            cmd = "cp %s %s"%(event.src_path,destinations[idx])
                            print(cmd)
                            os.system(cmd)
                else:
                    if key not in files_mul:
                        files_mul[key] = [event.src_path]
                    else:
                        files_mul[key] = files_mul[key] + [event.src_path]
                    print('-------------')
                    print(files_mul[key])
                    print(next_IPs)
                    print(self_name)
                    print(self_ip)
                    if len(files_mul[key]) == len(next_IPs):
                        for idx,ip in enumerate(next_IPs):
                            print(files_mul[key][idx])
                            print(next_tasks_map[task_name][idx])
                            current_file = files_mul[key][idx].split('/')[-1]
                            print(current_file)
                            destinations = "/centralized_scheduler/input/" +current_file +"#"+next_tasks_map[task_name][idx]
                            print(destinations)
                            if self_ip!=ip:
                                transfer_data(ip,username,password,files_mul[key][idx], destinations)
                            else: 
                                cmd = "cp %s %s"%(files_mul[key][idx],destinations)
                                print(cmd)
                                os.system(cmd)
            

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
            
            home_id = new_file.split('#')[1]
            task_name = new_file.split('#')[2]
            input_name = retrieve_input_enter(task_name, file_name)
            runtime_info = 'rt_enter '+ input_name + ' '+str(ts)
            key = (task_name,input_name)
            send_runtime_profile_computingnode(runtime_info,task_name)

    
            
            flag = dag[task_name][0] 
            task_flag = dag[task_name][1] 
            print('&&&&&&&&&&&&&&&&&&&&')
            print(dag[task_name])
            print(flag)

            if key not in task_mul:
                task_mul[key] = [new_file]
                count_mul[key]= int(flag)-1
                size_mul[key] = cal_file_size(event.src_path)
                next_mul[key] = [task_flag]
            else:
                task_mul[key] = task_mul[key] + [new_file]
                count_mul[key]=count_mul[key]-1
                size_mul[key] = size_mul[key] + cal_file_size(event.src_path)

            if count_mul[key] == 0: # enough input files
                incoming_file = task_mul[key]
                if len(incoming_file)==1: 
                    filenames = incoming_file[0]
                else:
                    filenames = incoming_file
                print('Add task to the processing queue')
                queue_mul[key] = False 
                

                input_path = os.path.split(event.src_path)[0]
                output_path = os.path.join(os.path.split(input_path)[0],'output')
                output_path = os.path.join(output_path,home_id,task_name)
                print('!!!!!!!!!')
                print(input_name)
                execute_task(task_name,input_name, filenames, input_path, output_path)
                #execute_task(task_name,file_name, filenames, input_path, output_path)
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

    #monitor INPUT as another process
    w=Watcher()
    w.start()

    #monitor OUTPUT in this process
    w1=Watcher1()
    w1.run()

    
    

if __name__ == '__main__':
    main()