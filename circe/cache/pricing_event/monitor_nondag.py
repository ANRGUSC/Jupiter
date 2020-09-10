#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on every node of the system.
"""

__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "4.0"

import sys
sys.path.append("../")
import multiprocessing
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import sys
import time
import json
import paramiko
from scp import SCPClient
import datetime
from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
import netifaces as ni
import platform
from os import path
from socket import gethostbyname, gaierror, error
import multiprocessing
import time
import urllib
import urllib.request
import configparser
import numpy as np
from collections import defaultdict
from multiprocessing import Process, Manager
import multiprocessing
from flask import Flask, request
from readconfig import read_config

global bottleneck
bottleneck = defaultdict(list)

app = Flask(__name__)

def tic():
    return time.time()

def toc(t):
    texec = time.time() - t
    print('Execution time is:'+str(texec))
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
        params = {'msg': msg, "work_node": node_id, "task_name": task_name}
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
    ts = -1
    while retry < num_retries:
        try:
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, IP, destination)
            os.system(cmd)
            print('data transfer complete\n')
            ts = time.time()
            s = "{:<10} {:<10} {:<10} {:<10} \n".format(node_name, transfer_type,source,ts)
            runtime_sender_log.write(s)
            runtime_sender_log.flush()
            break
        except:
            print('profiler_worker.txt: SSH Connection refused or File transfer failed, will retry in 2 seconds')
            time.sleep(2)
            retry += 1
    if retry == num_retries:
        s = "{:<10} {:<10} {:<10} {:<10} \n".format(node_name,transfer_type,source,ts)
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
    
    if TRANSFER == 0:
        return transfer_data_scp(IP,user,pword,source, destination)

    return transfer_data_scp(IP,user,pword,source, destination) #default

def multicast_data_scp(IP_list,user_list,pword_list,source, destination):
    """Transfer data using SCP to multiple nodes
    
    Args:
        IP (str): destination IP address list
        user (str): username list
        pword (str): password list
        source (str): source file path 
        destination (str): destination file path
    """
    #Keep retrying in case the containers are still building/booting up on
    #the child nodes.
    for idx, IP in enumerate(IP_list):
        retry = 0
        ts = -1
        while retry < num_retries:
            try:
                cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword_list[idx], ssh_port, source, user_list[idx], IP_list[idx], destination)
                os.system(cmd)
                print('data transfer complete\n')
                ts = time.time()
                s = "{:<10} {:<10} {:<10} {:<10} \n".format(node_name, transfer_type,source,ts)
                runtime_sender_log.write(s)
                runtime_sender_log.flush()
                break
            except:
                print('profiler_worker.txt: SSH Connection refused or File transfer failed, will retry in 2 seconds')
                time.sleep(2)
                retry += 1
        if retry == num_retries:
            s = "{:<10} {:<10} {:<10} {:<10} \n".format(node_name,transfer_type,source,ts)
            runtime_sender_log.write(s)
            runtime_sender_log.flush()

def multicast_data(IP_list,user_list,pword_list,source, destination):
    """Transfer data with given parameters
    
    Args:
        IP (str): destination IP 
        user (str): destination username
        pword (str): destination password
        source (str): source file path
        destination (str): destination file path
    """
    for IP,idx in enumerate(IP_list):
        msg = 'Transfer to IP: %s , username: %s , password: %s, source path: %s , destination path: %s'%(IP_list[idx],user_list[idx],pword_list[idx],source, destination)
    if TRANSFER==0:
        return multicast_data_scp
    return multicast_data_scp

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



def request_best_assignment(home_id,task_name,file_name):
    """Request the best computing node for the task
    
    Args:
        home_id (str): id of the home
        task_name (str): name of the current task
        file_name (str): name of the current processed file
    
    """
    try:
        url = "http://" + controllers_ip_map[task_name] + ":" + str(FLASK_SVC) + "/receive_best_assignment_request"
        params = {'home_id':home_id,'node_name':node_id,'file_name':file_name,'key':my_task}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending assignment request to flask server on controller node FAILED!!!")
        print(e)
        return "not ok"

def receive_best_assignment():
    """
        Receive the best computing node for the task
    """
    
    try:
        home_id = request.args.get('home_id')
        task_name = request.args.get('task_name')
        file_name = request.args.get('file_name')
        best_computing_node = request.args.get('best_computing_node')
        task_node_map[home_id,task_name,file_name] = best_computing_node      
        update_best[home_id,task_name,file_name] = True
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
            

            global files_out

            #based on flag2 decide whether to send one output to all children or different outputs to different children in
            #order given in the config file
            flag2 = sys.argv[2]

            task_name = event.src_path.split('/')[-3]
            home_id = event.src_path.split('/')[-2]
            input_name = retrieve_input_finish(task_name, temp_name)
            ts = time.time()
            runtime_info = 'rt_finish '+ input_name + ' '+str(ts)
            send_runtime_profile_computingnode(runtime_info,task_name,home_id)
            if sys.argv[3] in home_ids:
                IPaddr = sys.argv[4]
                user = sys.argv[5]
                password=sys.argv[6]
                source = event.src_path
                destination = os.path.join('/output', new_file)
                transfer_data(IPaddr,user,password,source, destination)
            elif flag2 == 'true':
                for i in range(3, len(sys.argv)-1,4):
                    next_task = sys.argv[i]
                    IPaddr = sys.argv[i+1]
                    user = sys.argv[i+2]
                    password = sys.argv[i+3]
                    # if IPaddr in super_task_ips_map:
                    if next_task in super_tasks:
                        destination = "/centralized_scheduler/input/" +next_task + "/"+home_id+"/"+new_file 
                        transfer_data(IPaddr,user,password,event.src_path, destination)
                    elif next_task in non_tasks:
                        print('non_tasks : Do nothing')
                    else:
                        key = (home_id,next_task,input_name)
                        while key not in task_node_map:
                            request_best_assignment(home_id,next_task,input_name)
                            print('--- waiting for computing node assignment')
                            time.sleep(3)
                        best_ip = computing_ip_map[task_node_map[key]]
                        destination = "/centralized_scheduler/input/" +next_task + "/"+home_id+"/"+new_file 
                        transfer_data(best_ip,user,password,event.src_path, destination)
                        

            else:
                num_child = (len(sys.argv) - 4) / 4
                files_out.append(new_file)
                if (len(files_out) == num_child):

                
                    for i in range(3, len(sys.argv)-1,4):
                        myfile = files_out.pop(0)
                        event_path = os.path.join(''.join(os.path.split(event.src_path)[:-1]), myfile)
                        IPaddr = sys.argv[i+1]
                        user = sys.argv[i+2]
                        password = sys.argv[i+3]
                        
                        if IPaddr in super_task_ips_map:
                            destination = "/centralized_scheduler/input/" +super_task_ips_map[IPaddr] + "/"+home_id+"/"+new_file 

                            transfer_data(IPaddr,user,password,event.src_path, destination)
                        elif IPaddr in non_tasks_ips_map:
                            print('non_tasks : Do nothing')
                        else:
                            best_ip = task_node_map[next_tasks_map[task_name][i]]
                            destination = "/centralized_scheduler/input/" +next_tasks_map[task_name][i]+"/"+home_id+"/"+myfile
                            transfer_data(best_ip,user,password,event.src_path, destination)

                    files_out=[]


#for INPUT folder
class Watcher(multiprocessing.Process):

    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'input/')
    
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.observer = Observer()

    def run(self):
        """
            Continuously watching the ``INPUT`` folder.
            When file in the input folder is received, based on the DAG info imported previously, it either waits for more input files, or  perform the current task on the current node.
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


            """
                Save the time when an input file is available. This is taken as the start time of the task.
                The output time is stored in the file central_scheduler/runtime/droplet_runtime_input_(%node name)
            """
            
            new_file = os.path.split(event.src_path)[-1]
            if '_' in new_file:
                temp_name = new_file.split('_')[0]
            else:
                temp_name = new_file.split('.')[0]


            task_name = event.src_path.split('/')[-3]
            home_id = event.src_path.split('/')[-2]
            input_name = retrieve_input_enter(task_name, temp_name)

            queue_mul.put(new_file)
            
            ts = time.time()
            if RUNTIME == 1:
                s = "{:<10} {:<10} {:<10} {:<10} \n".format(node_name,transfer_type,event.src_path,ts)
                runtime_receiver_log.write(s)
                runtime_receiver_log.flush()

            """
                Save the time the input file enters the queue
            """
            filename = new_file
            global filenames

            if len(filenames) == 0:
                runtime_info = 'rt_enter '+ input_name+ ' '+str(ts)
                send_runtime_profile_computingnode(runtime_info,task_name,home_id)
                for next_task in next_tasks_map[task_name]:
                    update_best[home_id,next_task,input_name]= False

            flag1 = sys.argv[1]
            if flag1 == "1":
                # Start msg
                ts = time.time()
                runtime_info = 'rt_exec '+ input_name+ ' '+str(ts)
                send_runtime_profile_computingnode(runtime_info,task_name,home_id)
                inputfile=queue_mul.get()
                input_path = os.path.split(event.src_path)[0]
                output_path = input_path.replace("input","output")
                dag_task = multiprocessing.Process(target=taskmodule.task, args=(inputfile, input_path, output_path))
                dag_task.start()
                dag_task.join()
                ts = time.time()
                runtime_info = 'rt_finish '+ input_name+ ' '+str(ts)
                send_runtime_profile_computingnode(runtime_info,task_name,home_id)
            else:
                filenames.append(queue_mul.get())
                if (len(filenames) == int(flag1)):
                    ts = time.time()
                    runtime_info = 'rt_exec '+ input_name+ ' '+str(ts)
                    send_runtime_profile_computingnode(runtime_info,task_name,home_id)
                    
                    input_path = os.path.split(event.src_path)[0]
                    output_path = input_path.replace("input","output")
                    

                    dag_task = multiprocessing.Process(target=taskmodule.task, args=(filenames, input_path, output_path))
                    dag_task.start()
                    dag_task.join()
                    filenames = []
                    ts = time.time()
                    runtime_info = 'rt_finish '+ input_name+ ' '+str(ts)
                    send_runtime_profile_computingnode(runtime_info,task_name,home_id)
                
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

    # Prepare transfer-runtime file:
    global runtime_sender_log, RUNTIME, TRANSFER, FLASK_DOCKER,transfer_type
    RUNTIME = int(config['CONFIG']['RUNTIME'])
    TRANSFER = int(config['CONFIG']['TRANSFER'])
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])

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

    global FLASK_SVC, MONGO_PORT, username,password,ssh_port, num_retries, queue_mul

    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT  = int(config['PORT']['MONGO_DOCKER'])
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])

    global controllers_ip_map, task_controllers, task_controllers_ips

    task_controllers = os.environ['ALL_NODES'].split(':')
    task_controllers_ips = os.environ['ALL_NODES_IPS'].split(':')
    controllers_ip_map = dict(zip(task_controllers, task_controllers_ips))


    global taskmap, taskname, taskmodule, filenames,files_out, node_name,node_id,all_nodes, all_nodes_ips

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
    node_name = os.environ['NODE_NAME']
    node_id = os.environ['NODE_ID']

    global home_ip_map, home_node_host_ports, home_ids,  home_ips,my_task

    home_nodes = os.environ['HOME_NODE'].split(' ')
    home_ids = [x.split(':')[0] for x in home_nodes]
    home_ips = [x.split(':')[1] for x in home_nodes]
    home_ip_map = dict(zip(home_ids, home_ips))
    
    home_node_host_ports = dict()
    for home_id in home_ids:
        home_node_host_ports[home_id] = home_ip_map[home_id] + ":" + str(FLASK_SVC)

    my_task = os.environ["TASK"]

    cmd = "mkdir centralized_scheduler/output/"+my_task
    os.system(cmd)
    for home_id in home_ids:
        cmd = "mkdir centralized_scheduler/output/"+my_task+"/" + home_id
        os.system(cmd)

    
    cmd = "mkdir centralized_scheduler/input/"+my_task 
    os.system(cmd)
    for home_id in home_ids:
        cmd = "mkdir centralized_scheduler/input/"+my_task+"/" + home_id
        os.system(cmd)


    all_nodes = os.environ["ALL_NODES"].split(":")
    all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":")

    global tasks, task_order, super_tasks, non_tasks
    tasks, task_order, super_tasks, non_tasks = get_taskmap()

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


    global manager,task_node_map, computing_ip_map, super_task_ips_map, non_tasks_ips_map,update_best

    computing_nodes = os.environ['ALL_COMPUTING_NODES'].split(':')
    computing_ips = os.environ['ALL_COMPUTING_IPS'].split(':')

    computing_ip_map = dict(zip(computing_nodes, computing_ips))

    manager = Manager()
    task_node_map = manager.dict()
    super_task_ips_map = dict()
    non_tasks_ips_map = dict()
    update_best = dict()

    for home_id in home_ids:
        task_node_map[home_id]  = home_id
    for idx, task in enumerate(all_nodes):
        if task in super_tasks:
            super_task_ips_map[all_nodes_ips[idx]] = task
        elif task in non_tasks:
            non_tasks_ips_map[all_nodes_ips[idx]] = task
    dag_file = '/centralized_scheduler/dag.txt'
    dag_info = k8s_read_dag(dag_file)
    dag = dag_info[1]

    global next_tasks_map
    next_tasks_map = dict()
    for task in dag:
        next_tasks_map[task] = dag[task][2:]

    for home_id in home_ids:
        next_tasks_map[home_id] = [os.environ['CHILD_NODES']]

    web_server = MonitorRecv()
    web_server.start()

    if taskmap[1] == True:
        queue_mul=multiprocessing.Queue()

        #monitor INPUT as another process
        w=Watcher()
        w.start()

        #monitor OUTPUT in this process
        w1=Watcher1()
        w1.run()
    else:

        print(taskmap[2:])
        path_src = "/centralized_scheduler/" + taskname
        args = ' '.join(str(x) for x in taskmap[2:])

        if os.path.isfile(path_src + ".py"):
            cmd = "python3 -u " + path_src + ".py " + args          
        else:
            cmd = "sh " + path_src + ".sh " + args
        os.system(cmd)

if __name__ == '__main__':
    main()
    
