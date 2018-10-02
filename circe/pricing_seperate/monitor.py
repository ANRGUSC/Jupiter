#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on every node of the system.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, Aleksandra Knezevic, Pranav Sakulkar, Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
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
import urllib.request
from urllib import parse
import configparser
from multiprocessing import Process, Manager
from flask import Flask, request
import _thread
import threading
import numpy as np



app = Flask(__name__)

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
        file_name = pricing_info[0]
        node_name = pricing_info[1]
        node_ip = pricing_info[2]
        print("Received pricing info")
        #Node name, Network, CPU, Memory, Queue
        price_info = [node_name,float(pricing_info[3]),float(pricing_info[4]),float(pricing_info[5]),float(pricing_info[6])]
        if file_name not in task_price_summary:
            task_price_count[file_name] = 1
            task_price_summary[file_name] = [price_info]
            
            
        else:
            task_price_count[file_name] = task_price_count[file_name] +1
            task_price_summary[file_name] = task_price_summary[file_name] + [price_info]
    
        print(task_price_count)
        print(task_price_summary)

        print('-------------')
        
    except Exception as e:
        print("Bad reception or failed processing in Flask for pricing announcement: "+ e) 
        return "not ok" 

    return "ok"
app.add_url_rule('/receive_price_info', 'receive_price_info', receive_price_info)


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
    print(IP)
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
    print(msg)
    

    if TRANSFER == 0:
        return transfer_data_scp(IP,user,pword,source, destination)

    return transfer_data_scp(IP,user,pword,source, destination) #default
    


def pricing_to_best_node_mapping(pricing_func):
    """Mapping the chosen price calculation method based on ``jupiter_config.PRICE_OPTION`` in ``jupiter_config.ini``
    
    Args:
        PRICE_OPTION (int, optional): PRICE_OPTION specified from ``jupiter_config.ini``, default method is sum
    
    Returns:
        function: chosen price calculation method

    """
    
    def select_best_node(task_price_summary,file_name):
        """Select the best node from price information of all nodes
        
        Args:
            task_price_summary: price information of all nodes
            file_name (str): Incoming file name
        """
        cost_list = pricing_func(task_price_summary, file_name)
        best_node = min(cost_list,key=cost_list.get)
        print(best_node)
        return best_node

    return select_best_node


@pricing_to_best_node_mapping
def sum_best_node(task_price_summary, file_name):
    w_net = 1 # Network
    w_cpu = 1 # Resource
    w_mem = 1 # Resource
    w_queue = 1 # Execution time=
    cost_list = dict()
    for item in task_price_summary[file_name]:
        cost_list[item[0]] = item[1]*w_net +  item[2]*w_cpu + item[3]*w_mem + item[4]*w_queue
    return cost_list


@pricing_to_best_node_mapping
def max_best_node(task_price_summary, file_name):
    cost_list = dict()
    for item in task_price_summary[file_name]:
        cost_list[item[0]] = max(item[1:])
    return cost_list

def select_best_node(task_price_summary,file_name):
    """Select the best node from price information of all nodes
    
    Args:
        task_price_summary: price information of all nodes
        file_name (str): Incoming file name
    """

    if PRICE_OPTION == 1:
        return sum_best_node(task_price_summary, file_name)
    elif PRICE_OPTION == 2:
        return max_best_node(task_price_summary, file_name)
    


    msg = 'Select the best node for file %s'%(file_name)
    print(msg)

def setup_exec_node():
    """Setup prepared for the chosen computing node, transfer input files
    
    Args:
        chosen_node (TYPE): node having best price
        file_name (str): Incoming file name
        task_name (str): Incoming task name
    """
    global task_price_summary, task_price_count
    while True:
        time.sleep(30)
        if len(task_price_summary) == 0:
            print('*** No price information')
            continue
        processed_files = [k for k,v in task_price_count.items() if v == num_computing_nodes]
        print(processed_files)
        if len(processed_files) == 0:
            print('*** Not enough price information')
            continue
        for f in processed_files:
            print('*** Getting enough pricing announcement from all the computing nodes')
            
            best_node = select_best_node(task_price_summary,f)
            
            print('Most suitable node: ' + str(best_node))
            
            source_list = [("/centralized_scheduler/input/"+f) for f in task_mul[f]]

            print('Transfer the files to the corresponding destination')

            flag2 = sys.argv[2]
            global files_out

            #if you are sending the final output back to scheduler
            if sys.argv[3] == 'home':

                # IPaddr = sys.argv[4]
                # user = sys.argv[5]
                # password=sys.argv[6]

                
                destination_list = [(s+"#"+taskname+"#"+self_ip+"#"+'home') for s in source_list]


            elif flag2 == 'true':
                next_IPs = []
                for i in range(3, len(sys.argv)-1,4):
                    next_IPs.append(sys.argv[i+1])

                next_IP_list = '#'.join(next_IPs)

                destination_list = [(s+"#"+taskname+"#"+self_ip+"#"+flag2+"#"+ next_IP_list) for s in source_list]
                print(destination_list)
                    # user = sys.argv[i+2]
                    # password = sys.argv[i+3]


            else:
                num_child = (len(sys.argv) - 4) / 4
                files_out.append(new_file)
                next_IPs = []

                if (len(files_out) == num_child):
                    for i in range(3, len(sys.argv)-1,4):
                        myfile = files_out.pop(0)
                        event_path = os.path.join(''.join(os.path.split(event.src_path)[:-1]), myfile)
                        next_IPs = next_IPs.append(sys.argv[i+1])

                next_IP_list = '#'.join(next_IPs)

                destination_list = [(s+"#"+taskname+"#"+self_ip+"#"+flag2+"#"+ next_IP_list) for s in source_list]
                print(destination_list)

                files_out=[]
            
            
            ts = time.time()
            runtime_info = 'rt_exec '+ f+ ' '+str(ts)
            
            send_runtime_profile(runtime_info,taskname)
            for idx,source in enumerate(source_list):
                print(idx)
                print(source)
                transfer_data(node_ip_map[best_node],username,password,source, destination_list[idx])
            del task_price_summary[f]
            del task_price_count[f]
        
def send_monitor_data(msg):
    """
    Sending message to flask server on home

    Args:
        msg (str): the message to be sent

    Returns:
        str: the message if successful, "not ok" otherwise.

    Raises:
        Exception: if sending message to flask server on home is failed
    """
    try:
        print("Sending message", msg)
        url = "http://" + home_node_host_port + "/recv_monitor_data"
        params = {'msg': msg, "work_node": taskname}
        params = parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending message to flask server on home FAILED!!!")
        print(e)
        return "not ok"
    return res

def send_runtime_profile(msg,taskname):
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
        url = "http://" + home_node_host_port + "/recv_runtime_profile"
        params = {'msg': msg, "work_node": taskname}
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

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)


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

            #if you are sending the final output back to scheduler
            if sys.argv[3] == 'home':
                
                ts = time.time()
                print('++++++++++++++++++++++++++')
                print(temp_name)
                runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                print(event.src_path)
                send_runtime_profile(runtime_info,taskname)

                IPaddr = sys.argv[4]
                user = sys.argv[5]
                password=sys.argv[6]

                transfer_data(IPaddr,user,password,event.src_path, os.path.join('/output', new_file))

                # ssh = paramiko.SSHClient()
                # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # #Keep retrying in case the containers are still building/booting up on
                # #the child nodes.
                # retry = 0
                # while retry < num_retries:
                #     try:
                #         ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                #         sftp = ssh.open_sftp()
                #         sftp.put(event.src_path, os.path.join('/output', new_file))
                #         sftp.close()
                #         break
                #     except:
                #         print('SSH Connection refused or File tranfer failed, will retry in 2 seconds')
                #         time.sleep(2)
                #         retry += 1
                
                # ssh.close()

            elif flag2 == 'true':

                ts = time.time()
                print('+++++++++++++++++++++++++++++++++++++++++++')
                print(temp_name)
                runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info,taskname)
                print(event.src_path)

                for i in range(3, len(sys.argv)-1,4):
                    IPaddr = sys.argv[i+1]
                    user = sys.argv[i+2]
                    password = sys.argv[i+3]

                    transfer_data(IPaddr,user,password,event.src_path,  os.path.join('/centralized_scheduler', 'input', new_file))

                    #port = int(sys.argv[i+4])

                    # ssh = paramiko.SSHClient()
                    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    # #Keep retrying in case the containers are still building/booting up on
                    # #the child nodes.
                    # retry = 0
                    # while retry < num_retries:
                    #     try:
                    #         ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                    #         sftp = ssh.open_sftp()
                    #         sftp.put(event.src_path, os.path.join('/centralized_scheduler', 'input', new_file))
                    #         sftp.close()
                    #         break
                    #     except:
                    #         print('SSH Connection refused or File transfer failed, will retry in 2 seconds')
                    #         time.sleep(2)
                    #         retry += 1

                    # ssh.close()


            else:
                num_child = (len(sys.argv) - 4) / 4
                files_out.append(new_file)

                if (len(files_out) == num_child):

                    ts = time.time()
                    print('++++++++++++++++++++++++++++++++++++')
                    print(temp_name)
                    runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                    send_runtime_profile(runtime_info,taskname)
                    print(event.src_path)
                        
                    for i in range(3, len(sys.argv)-1,4):
                        myfile = files_out.pop(0)
                        event_path = os.path.join(''.join(os.path.split(event.src_path)[:-1]), myfile)
                        IPaddr = sys.argv[i+1]
                        user = sys.argv[i+2]
                        password = sys.argv[i+3]

                        transfer_data(IPaddr,user,password,event_path,  os.path.join('/centralized_scheduler','input', myfile))
                        #port = int(sys.argv[i+4])

                        # ssh = paramiko.SSHClient()
                        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                        # #Keep retrying in case the containers are still building/booting up on
                        # #the child nodes.
                        # retry = 0
                        # while retry < num_retries:
                        #     try:
                        #         ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                        #         sftp = ssh.open_sftp()
                        #         sftp.put(event_path, os.path.join('/centralized_scheduler','input', myfile))
                        #         sftp.close()
                        #         break
                        #     except:
                        #         print('SSH Connection refused or File transfer failed, will retry in 2 seconds')
                        #         time.sleep(2)
                        #         retry += 1
                
                        
                        # ssh.close()

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
                temp_name = new_file.split('_')[0]
            else:
                temp_name = new_file.split('.')[0]

            
            ts = time.time()
            if RUNTIME == 1:
                s = "{:<10} {:<10} {:<10} {:<10} \n".format(node_name,transfer_type,event.src_path,ts)
                runtime_receiver_log.write(s)
                runtime_receiver_log.flush()
            """
                Save the time the input file enters the queue
            """
            
            flag1 = sys.argv[1]
            
            if temp_name not in task_mul:
                task_mul[temp_name] = [new_file]
                print('++++++++++++++++++++++')
                ts = time.time()
                print(temp_name)
                runtime_info = 'rt_enter '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info,taskname)
                print(event.src_path)
                count_dict[temp_name]=int(flag1)-1
            else:
                task_mul[temp_name] = task_mul[temp_name] + [new_file]
                count_dict[temp_name]=count_dict[temp_name]-1
            # print(task_mul[temp_name])
            

            if count_dict[temp_name] == 0: # enough input files
                filename = task_mul[temp_name]
                if len(filename)==1: 
                    filenames = filename[0]
                else:
                    filenames = filename    
               
                # When receive an input file, issue pricing request instead of performing the task
                # must check temp_name to ensure, for example: fusion case with multiple inputs from sample detector, astute detector, and others... 
                # print(filename)
                print('List of files')
                print(filenames)
                filepath = os.path.split(event.src_path)[0]
                # print(filepath)
                filepaths = [filepath+'/'+fname for fname in filename]
                # print(filepaths)
                output_data = [file_size(x) for x in filepaths]
                sum_output_data = sum(output_data)
                # print(dest_node_host_port_list)

                for dest_node_host_port in dest_node_host_port_list:
                    print(dest_node_host_port )
                    issue_price_request(dest_node_host_port,temp_name, sum_output_data)
                
                


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
    global PRICE_OPTION
    PRICE_OPTION          = int(config['CONFIG']['PRICE_OPTION'])


    global FLASK_SVC, FLASK_DOCKER, MONGO_PORT, username,password,ssh_port, num_retries, task_mul, count_dict,self_ip

    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT  = int(config['PORT']['MONGO_DOCKER'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    self_ip     = os.environ['OWN_IP']


    global taskmap, taskname, taskmodule, filenames,files_out, home_node_host_port
    global all_nodes, all_nodes_ips, node_id, node_name
    global all_computing_nodes,all_computing_ips, num_computing_nodes, node_ip_map

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
    home_node_host_port = os.environ['HOME_NODE'] + ":" + str(FLASK_SVC)

    all_computing_nodes = os.environ["ALL_COMPUTING_NODES"].split(":")
    all_computing_ips = os.environ["ALL_COMPUTING_IPS"].split(":")
    num_computing_nodes = len(all_computing_nodes)
    node_ip_map = dict(zip(all_computing_nodes, all_computing_ips))
    # print('Node IP mapping')
    # print(node_ip_map)

    # print('Number of computing nodes : '+ str(num_computing_nodes))

    global dest_node_host_port_list
    dest_node_host_port_list = [ip + ":" + str(FLASK_SVC) for ip in all_computing_ips]

    global task_price_summary, task_price_count
    manager = Manager()
    task_price_summary = manager.dict()
    task_price_count = manager.dict()

    web_server = MonitorRecv()
    web_server.start()

    _thread.start_new_thread(setup_exec_node,())

    if taskmap[1] == True:
        task_mul = manager.dict()
        count_dict = manager.dict()
        

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
        print(cmd)
        os.system(cmd)

if __name__ == '__main__':
    main()
    
