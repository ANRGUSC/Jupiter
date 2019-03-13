#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on the scheduler node of CIRCE. 

"""

__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import sys
sys.path.append("../")
import paramiko
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import json
from multiprocessing import Process, Manager
from readconfig import read_config
from socket import gethostbyname, gaierror, error

from watchdog.events import PatternMatchingEventHandler
import multiprocessing
from flask import Flask, request
from collections import defaultdict

from os import path
import configparser
import urllib
import _thread
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient




# End-to-end metrics
start_times = []
end_times = []
exec_times = []
count = 0

app = Flask(__name__)

# Per task times
start_time = defaultdict(list)
end_time = defaultdict(list)

rt_enter_time = defaultdict(list)
rt_exec_time = defaultdict(list)
rt_finish_time = defaultdict(list)

rt_enter_time_computingnode = defaultdict(list)
rt_exec_time_computingnode = defaultdict(list)
rt_finish_time_computingnode = defaultdict(list)

#@app.route('/recv_monitor_data')
def recv_mapping():
    """

    Receiving run-time profiling information from WAVE/HEFT for every task (task name, start time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """

    global start_time
    global end_time

    try:
        worker_node = request.args.get('work_node')
        msg = request.args.get('msg')
        ts = time.time()

        # print("Received flask message:", worker_node, msg, ts)

        if msg == 'start':
            start_time[worker_node].append(ts)
        else:
            end_time[worker_node].append(ts)
            print(worker_node + " takes time:" + str(end_time[worker_node][-1] - start_time[worker_node][-1]))
            if worker_node == "globalfusion":
                # Per task stats:
                print("Start time stats:", start_time)
                print("End time stats:", end_time)

    except Exception as e:
        print("Bad reception or failed processing in Flask")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_monitor_data', 'recv_mapping', recv_mapping)


def return_output_files():
    """
    Return number of output files
    
    Returns:
        int: number of output files
    """
    num_files = len(os.listdir("output/"))
    print("Recieved request for number of output files. Current done:", num_files)
    return json.dumps(num_files)
app.add_url_rule('/', 'return_output_files', return_output_files)


def receive_assignment_info():
    """
        Receive corresponding best nodes from the corresponding computing node
    """
    try:
        assignment_info = request.args.get('assignment_info').split('#')
        # print("-----------Received assignment info")
        task_node_summary[assignment_info[0]] = assignment_info[1]
        print(task_node_summary)

    except Exception as e:
        print("Bad reception or failed processing in Flask for assignment announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_assignment_info', 'receive_assignment_info', receive_assignment_info)

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

def recv_runtime_profile():
    """

    Receiving run-time profiling information for every task (task name, start time stats, waiting time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """

    global rt_enter_time
    global rt_exec_time
    global rt_finish_time

    try:
        worker_node = request.args.get('work_node')
        msg = request.args.get('msg').split()
        

        print("Received flask message:", worker_node, msg[0],msg[1], msg[2])

        if msg[0] == 'rt_enter':
            rt_enter_time[(worker_node,msg[1])] = float(msg[2])
        elif msg[0] == 'rt_exec' :
            rt_exec_time[(worker_node,msg[1])] = float(msg[2])
        else: #rt_finish
            rt_finish_time[(worker_node,msg[1])] = float(msg[2])

            print('----------------------------')
            print("Worker node: "+ worker_node)
            print("Input file : "+ msg[1])
            print("Total duration time:" + str(rt_finish_time[(worker_node,msg[1])] - rt_enter_time[(worker_node,msg[1])]))
            print("Waiting time:" + str(rt_exec_time[(worker_node,msg[1])] - rt_enter_time[(worker_node,msg[1])]))
            print(worker_node + " execution time:" + str(rt_finish_time[(worker_node,msg[1])] - rt_exec_time[(worker_node,msg[1])]))
            
            print('----------------------------')  

            if worker_node == "globalfusion" or "task4":
                # Per task stats:
                print('********************************************') 
                print("Runtime profiling info:")
                """
                    - Worker node: task name
                    - Input file: input files
                    - Enter time: time the input file enter the queue
                    - Execute time: time the input file is processed
                    - Finish time: time the output file is generated
                    - Elapse time: total time since the input file is created till the output file is created
                    - Duration time: total execution time of the task
                    - Waiting time: total time since the input file is created till it is processed
                """
                log_file = open(os.path.join(os.path.dirname(__file__), 'runtime_tasks.txt'), "w")
                s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Task_name','local_input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time')
                print(s)
                log_file.write(s)
                for k, v in rt_enter_time.items():
                    worker, file = k
                    if k in rt_finish_time:
                        elapse = rt_finish_time[k]-v
                        duration = rt_finish_time[k]-rt_exec_time[k]
                        waiting = rt_exec_time[k]-v
                        s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(worker, file, v, rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting))
                        print(s)
                        log_file.write(s)
                        log_file.flush()

                log_file.close()
                print('********************************************')

                
    except Exception as e:
        print("Bad reception or failed processing in Flask for runtime profiling")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_runtime_profile', 'recv_runtime_profile', recv_runtime_profile)


def recv_runtime_profile_computingnode():
    """

    Receiving run-time profiling information for every task (task name, start time stats, waiting time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """

    global rt_enter_time_computingnode
    global rt_exec_time_computingnode
    global rt_finish_time_computingnode

    try:
        worker_node = request.args.get('work_node')
        msg = request.args.get('msg').split()
        task_name = request.args.get('task_name')
        

        print("Received flask message:", worker_node, msg[0],msg[1], msg[2],task_name)

        if msg[0] == 'rt_enter':
            rt_enter_time_computingnode[(worker_node,task_name,msg[1])] = float(msg[2])
        elif msg[0] == 'rt_exec' :
            rt_exec_time_computingnode[(worker_node,task_name,msg[1])] = float(msg[2])
        else: #rt_finish
            rt_finish_time_computingnode[(worker_node,task_name,msg[1])] = float(msg[2])

            print('----------------------------')
            print('Runtime info at each computing node')
            print("Worker node: "+ worker_node)
            print("Input file : "+ msg[1])
            print("Task name: " + task_name)
            print("Total duration time:" + str(rt_finish_time_computingnode[(worker_node,task_name, msg[1])] - rt_enter_time_computingnode[(worker_node,task_name, msg[1])]))
            print("Waiting time:" + str(rt_exec_time_computingnode[(worker_node,task_name,msg[1])] - rt_enter_time_computingnode[(worker_node,task_name,msg[1])]))
            print(worker_node + " execution time:" + str(rt_finish_time_computingnode[(worker_node,task_name,msg[1])] - rt_exec_time_computingnode[(worker_node,task_name,msg[1])]))
            
            print('----------------------------')  

            if task_name == "globalfusion" or "task4":
                # Per task stats:
                print(task_name)
                print('********************************************') 
                print("Runtime profiling computing node info:")
                """
                    - Worker node: task name
                    - Input file: input files
                    - Enter time: time the input file enter the queue
                    - Execute time: time the input file is processed
                    - Finish time: time the output file is generated
                    - Elapse time: total time since the input file is created till the output file is created
                    - Duration time: total execution time of the task
                    - Waiting time: total time since the input file is created till it is processed
                """
                log_file = open(os.path.join(os.path.dirname(__file__), 'runtime_tasks_computingnode.txt'), "w")
                s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Worker_node','Task_name','input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time')
                print(s)
                log_file.write(s)
                for k, v in rt_enter_time_computingnode.items():
                    worker, task, file = k
                    # print('***')
                    # print(k)
                    # print(v)
                    # print(worker)
                    # print(task)
                    # print(file)
                    # print(rt_finish_time_computingnode)
                    if k in rt_finish_time_computingnode:
                        elapse = rt_finish_time_computingnode[k]-v
                        duration = rt_finish_time_computingnode[k]-rt_exec_time_computingnode[k]
                        waiting = rt_exec_time_computingnode[k]-v
                        s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(worker, task, file, v, rt_exec_time_computingnode[k],rt_finish_time_computingnode[k],str(elapse),str(duration),str(waiting))
                        print(s)
                        log_file.write(s)
                        log_file.flush()

                log_file.close()
                print('********************************************')

                
    except Exception as e:
        print("Bad reception or failed processing in Flask for runtime profiling")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_runtime_profile_computingnode', 'recv_runtime_profile_computingnode', recv_runtime_profile_computingnode)

def transfer_data_scp(IP,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        IP (str): destination IP address
        user (str): username
        pword (str): password
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
            s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home', transfer_type,source,ts)
            runtime_sender_log.write(s)
            runtime_sender_log.flush()
            break
        except:
            print('profiler_worker.txt: SSH Connection refused or File transfer failed, will retry in 2 seconds')
            time.sleep(2)
            retry += 1
    if retry == num_retries:
        s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,source,ts)
        runtime_sender_log.write(s)
        runtime_sender_log.flush()

    

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
    

    if TRANSFER == 0:
        return transfer_data_scp(IP,user,pword,source, destination)

    return transfer_data_scp(IP,user,pword,source, destination) #default



def get_updated_network_profile():
    """Get updated network information from the network profilers
    
    Returns:
        TYPE: Description
    """
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
        # print('---------------------')
        for record in logging:
            # print('---')
            # print(record)
            # print(ip_profilers_map)
            # print(record['Destination[IP]'])
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            network_info[ip_profilers_map[record['Destination[IP]']]] = str(record['Parameters'])
        
        return network_info
    except Exception as e:
        print("Network request failed. Will try again, details: " + str(e))
        return -1

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

def price_estimate():
    """Calculate corresponding price (network) for home node only 

    Returns:
        float: calculated price
    """

    # Default values
    price = dict()
    price['network'] = sys.maxsize
    price['cpu'] = -1
    price['memory'] = -1 
    price['queue'] = -1

    """
    Input information:
        - Resource information: resource_info
        - Network information: network_info
        - Task queue: task_mul
        - Execution information: execution_info
    """

    try:
        
        # print(' Retrieve all input information: ')
        network_info = get_updated_network_profile()
        # print(network_info)
        test_size = cal_file_size('/centralized_scheduler/1botnet.ipsum')
        # print(test_size)
        # print('--- Network cost:----------- ')
        price['network'] = dict()
        for node in network_info:
            # print(network_info[node])
            computing_params = network_info[node].split(' ')
            # print(computing_params)
            computing_params = [float(x) for x in computing_params]
            # print(computing_params)
            p = (computing_params[0] * test_size * test_size) + (computing_params[1] * test_size) + computing_params[2]
            # print(p)
            # print(node)
            price['network'][node] = p
            
        # print(price['network'])
        print('-----------------')
        print('Overall price:')
        print(price)
        return price
             
    except:
        print('Error reading input information to calculate the price')
        
    return price



def announce_price(task_controller_ip, price):
    """Announce my current price to the corresponding task controller giving the task controller ip
    
    Args:
        task_controller_ip (str): IP of the task controller
        price : my current price
    """
    try:

        print("Announce my price")
        url = "http://" + task_controller_ip + ":" + str(FLASK_SVC) + "/receive_price_info"
        pricing_info = my_task+"#"+str(price['cpu'])+"#"+str(price['memory'])+"#"+str(price['queue'])
        for node in price['network']:
            # print(node)
            # print(price['network'][node])
            pricing_info = pricing_info + "$"+node+"%"+str(price['network'][node])
        
        print(pricing_info)
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
    """Push my price to the fist task controller
    """
    price = price_estimate() #to the first task only
    announce_price(controller_ip_map[first_task], price)

def schedule_update_price(interval):
    """Schedule the price update procedure every interval
    
    Args:
        interval (int): chosen interval (minutes)
    """
    sched = BackgroundScheduler()
    sched.add_job(push_updated_price,'interval',id='push_price', minutes=interval, replace_existing=True)
    sched.start()

def update_assignment_info_child(node_ip):
    """Update my best assigned compute node to the node given its IP
    
    Args:
        node_ip (str): IP of the node
    """
    try:
        print("Announce my current best computing node " + node_ip)
        url = "http://" + node_ip + ":" + str(FLASK_SVC) + "/update_assignment_info_child"
        assignment_info = self_task + "#"+task_node_summary[self_task]
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

def receive_best_assignment():
    """
        Receive the best computing node for the task
    """
    
    try:
        print("Received best assignment")
        home_id = request.args.get('home_id')
        task_name = request.args.get('task_name')
        file_name = request.args.get('file_name')
        best_computing_node = request.args.get('best_computing_node')
        task_node_summary[task_name,file_name] = best_computing_node
        # print(task_name)
        # print(best_computing_node)
        # print(task_node_summary)
        update_best[task_name,file_name] = True


    except Exception as e:
        update_best[task_name,file_name] = False
        print("Bad reception or failed processing in Flask for best assignment request: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_best_assignment', 'receive_best_assignment', receive_best_assignment)


class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)


class MyHandler(PatternMatchingEventHandler):
    """
    Handling the event when there is a new file generated in ``OUTPUT`` folder
    """

    def process(self, event):
        """
        Log the time the file is created and calculate the execution time whenever there is an event.
        
        Args:
            event: event to be watched for the ``OUTPUT`` folder
        """

        global start_times
        global end_times
        global exec_times
        global count
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        if event.event_type == 'created':
            end_times.append(time.time())
            print("ending time is: ", end_times)
            print("starting time is: ", start_times)
            exec_times.append(end_times[count] - start_times[count])

            print("execution time is: ", exec_times)
            # global count: number of output files
            count+=1

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


class Watcher:
    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'input/')

    def __init__(self):
        self.observer = Observer()

    def run(self):
        """
        Monitoring ``INPUT`` folder for the incoming files.
        
        You can manually place input files into the ``INPUT`` folder (which is under ``centralized_scheduler_with_task_profiler``):
        
            .. code-block:: bash
        
                mv 1botnet.ipsum input/
        
        Once the file is there, it sends the file to the node performing the first task.
        """

        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()

class Handler(FileSystemEventHandler):
    """
        Handling the event when there is a new file generated in ``INPUT`` folder
    """

    @staticmethod
    def on_any_event(event):
        """
        Whenever there is a new input file in ``INPUT`` folder, the function:

        - Log the time the file is created

        - Start the connection to the first scheduled node

        - Copy the newly created file to the ``INPUT`` folder of the first scheduled node
        
        Args:
            event (FileSystemEventHandler): monitored event
        """

        if event.is_directory:
            return None

        elif event.event_type == 'created':

            print("Received file as input - %s." % event.src_path)

            if RUNTIME == 1:   
                ts = time.time() 
                s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,event.src_path,ts)
                runtime_receiver_log.write(s)
                runtime_receiver_log.flush()

            start_times.append(time.time())
            print("start time is: ", start_times)
            new_file_name = os.path.split(event.src_path)[-1]


            print(first_task)
            print(task_node_summary)
            print(node_ip_map)

            while not task_node_summary:
                print('task node summary not yet available!!!')
                time.sleep(2)
                
            IP = node_ip_map[task_node_summary[first_task]]

            print(new_file_name)
            # new_file_name = new_file_name+"#"+my_task+"#"+first_task+"#"+first_flag
            # print(new_file_name)
            source = event.src_path
            destination = os.path.join('/centralized_scheduler', 'input', first_task,my_task,new_file_name)
            # destination = os.path.join('/centralized_scheduler', 'input', new_file_name)
            transfer_data(IP,username, password,source, destination)


def main():
    """
        -   Read configurations (DAG info, node info) from ``nodes.txt`` and ``configuration.txt``
        -   Monitor ``INPUT`` folder for the incoming files
        -   Whenever there is a new file showing up in ``INPUT`` folder, copy the file to the ``INPUT`` folder of the first scheduled node.
        -   Collect execution profiling information from the system.
    """

    ##
    ## Load all the confuguration
    ##
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    # Prepare transfer-runtime file:
    global runtime_sender_log, RUNTIME,TRANSFER, transfer_type
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

    global FLASK_DOCKER, FLASK_SVC, MONGO_SVC, username, password, ssh_port, num_retries, first_task

    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    FLASK_SVC      = int(config['PORT']['FLASK_SVC'])
    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    first_task  = os.environ['CHILD_NODES']

    global task_node_summary, controllers_id_map
    manager = Manager()
    task_node_summary = manager.dict()
    controllers_id_map = manager.dict()

    global all_computing_nodes,all_computing_ips, node_ip_map, first_flag,my_id, controller_ip_map, all_controller_nodes, all_controller_ips,my_task, self_profiler_ip, ip_profilers_map

    all_computing_nodes = os.environ["ALL_COMPUTING_NODES"].split(":")
    all_computing_ips = os.environ["ALL_COMPUTING_IPS"].split(":")
    num_computing_nodes = len(all_computing_nodes)
    node_ip_map = dict(zip(all_computing_nodes, all_computing_ips))

    all_controller_nodes = os.environ["ALL_NODES"].split(":")
    all_controller_ips = os.environ["ALL_NODES_IPS"].split(":")
    controller_ip_map = dict(zip(all_controller_nodes, all_controller_ips))

    profiler_ip = os.environ['ALL_PROFILERS'].split(' ')
    profiler_ip = [info.split(":") for info in profiler_ip]
    profiler_ip = profiler_ip[0][1:]

    profiler_nodes = os.environ['ALL_PROFILERS_NODES'].split(' ')
    profiler_nodes = [info.split(":") for info in profiler_nodes]
    profiler_nodes = profiler_nodes[0][1:]
    ip_profilers_map = dict(zip(profiler_ip, profiler_nodes))
    # print('############')
    # print(ip_profilers_map)

    my_id = os.environ['TASK']
    my_task = my_id.split('-')[1]

    self_profiler_ip = os.environ['SELF_PROFILER_IP']

    # print('***********')
    # print(my_id)
    

    path1 = 'configuration.txt'
    path2 = 'nodes.txt'
    dag_info = read_config(path1,path2)

    #get DAG and home machine info
    # first_task = dag_info[0]
    dag = dag_info[1]
    hosts=dag_info[2]
    first_flag = dag_info[1][first_task][1]

    print("TASK: ", dag_info[0])
    print("DAG: ", dag_info[1])
    print("HOSTS: ", dag_info[2])


    #monitor INPUT folder for the incoming files
    w = Watcher()
    w.run()

    web_server = MonitorRecv()
    web_server.start()

    update_interval = 3
    _thread.start_new_thread(schedule_update_price,(update_interval,))

    print("Starting the output monitoring system:")
    observer = Observer()
    observer.schedule(MyHandler(), path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'output/'))
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


    
    
if __name__ == '__main__':

    main()