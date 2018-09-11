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

def issue_price_request(dest_node_host_port,file_name, file_size):
    """Issue pricing request to every computing node
    
    Args:
        dest_node_host_port (str): destination node and Flask port
        file_name (str): incoming file name
        file_size (int): size of incoming file
    
    Returns:
        str: the message if successful, "not ok" otherwise.
    
    Raises:
        Exception: if sending message to flask server on home is failed
    """
    try:
        print("Sending pricing request :"+ file_name + ":"+ dest_node_host_port)
        url = "http://" + dest_node_host_port + "/receive_price_request"
        params = {'file_name':file_name ,'file_size':file_size, "task_name": taskname,"task_ip":self_ip,"node_name": node_id}
        params = parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending pricing request to flask server on computing node FAILED!!!")
        print(e)
        return "not ok"
    return res

def receive_price_info():
    """
        Receive price from every computing node, choose the most suitable computing node 
    """
    try:
        pricing_info = request.args.get('pricing_info').split('#')
        file_name = pricing_info[0]
        node_name = pricing_info[1]
        node_ip = pricing_info[2]
        price = float(pricing_info[3])
        # file_name = request.args.get('file_name')
        # node_name = request.args.get('node_name')
        # node_ip = request.args.get('node_ip')
        # price = float(request.args.get('price'))
        print("Received pricing info: ", file_name,node_name, node_ip,price)
        if file_name not in task_price_summary:
            task_price_count[file_name] = 1
            task_price_summary[file_name] = [node_name,price]
        else:
            task_price_count[file_name] = task_price_count[file_name] +1
            task_price_summary[file_name]=task_price_summary[file_name]+[node_name,price]
        # print(task_price_summary)
        # print(task_price_count)

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
        for file in processed_files:
            print('*** Getting enough pricing announcement from all the computing nodes')
            # print(file)
            # print(task_price_summary[file])
            best_idx = np.argmin(task_price_summary[file][1::2])
            # print(task_price_summary[file][1::2][best_idx])
            best_node = task_price_summary[file][::2][best_idx]
            # print(task_price_summary[file][::2])
            print('Most suitable node: ' + best_node)
            
            # print(source)
            # print(destination)
            # print(node_ip_map)
            print(task_mul)
            print(task_mul[file])
            # source = "/centralized_scheduler/input/"+file
            # destination = source+"#"+taskname+"#"+self_ip
            source_list = [("/centralized_scheduler/input/"+f) for f in task_mul[file]]
            destination_list = [(s+"#"+taskname+"#"+self_ip) for s in source_list]
            # print(source_list)
            # print(destination_list)
            # print(file)
            ts = time.time()
            runtime_info = 'rt_exec '+ file+ ' '+str(ts)
            send_runtime_profile(runtime_info)
            for idx,source in enumerate(source_list):
                print(idx)
                print(source)
                transfer_data_scp(node_ip_map[best_node],username,password,source, destination_list[idx])
            del task_price_summary[file]
            del task_price_count[file]
        # just for testing
        # print('Send 2nd file for testing')
        # os.system("cp /centralized_scheduler/sample_input/2botnet.ipsum /centralized_scheduler/input/")
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

def send_runtime_profile(msg):
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
            

            

            # send_runtime_profile(runtime_info)
                
            global files_out

            #based on flag2 decide whether to send one output to all children or different outputs to different children in
            #order given in the config file
            flag2 = sys.argv[2]

            #if you are sending the final output back to scheduler
            if sys.argv[3] == 'home':
                
                ts = time.time()
                runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info)

                IPaddr = sys.argv[4]
                user = sys.argv[5]
                password=sys.argv[6]
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                #Keep retrying in case the containers are still building/booting up on
                #the child nodes.
                retry = 0
                while retry < num_retries:
                    try:
                        ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                        sftp = ssh.open_sftp()
                        sftp.put(event.src_path, os.path.join('/output', new_file))
                        sftp.close()
                        break
                    except:
                        print('SSH Connection refused or File tranfer failed, will retry in 2 seconds')
                        time.sleep(2)
                        retry += 1
                
                ssh.close()

            elif flag2 == 'true':

                ts = time.time()
                runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info)

                for i in range(3, len(sys.argv)-1,4):
                    IPaddr = sys.argv[i+1]
                    user = sys.argv[i+2]
                    password = sys.argv[i+3]
                    #port = int(sys.argv[i+4])

                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    #Keep retrying in case the containers are still building/booting up on
                    #the child nodes.
                    retry = 0
                    while retry < num_retries:
                        try:
                            ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                            sftp = ssh.open_sftp()
                            sftp.put(event.src_path, os.path.join('/centralized_scheduler', 'input', new_file))
                            sftp.close()
                            break
                        except:
                            print('SSH Connection refused or File transfer failed, will retry in 2 seconds')
                            time.sleep(2)
                            retry += 1

                    ssh.close()


            else:
                num_child = (len(sys.argv) - 4) / 4
                files_out.append(new_file)

                if (len(files_out) == num_child):

                    ts = time.time()
                    runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                    send_runtime_profile(runtime_info)
                        
                    for i in range(3, len(sys.argv)-1,4):
                        myfile = files_out.pop(0)
                        event_path = os.path.join(''.join(os.path.split(event.src_path)[:-1]), myfile)
                        IPaddr = sys.argv[i+1]
                        user = sys.argv[i+2]
                        password = sys.argv[i+3]
                        #port = int(sys.argv[i+4])

                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                        #Keep retrying in case the containers are still building/booting up on
                        #the child nodes.
                        retry = 0
                        while retry < num_retries:
                            try:
                                ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                                sftp = ssh.open_sftp()
                                sftp.put(event_path, os.path.join('/centralized_scheduler','input', myfile))
                                sftp.close()
                                break
                            except:
                                print('SSH Connection refused or File transfer failed, will retry in 2 seconds')
                                time.sleep(2)
                                retry += 1
                
                        
                        ssh.close()

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
            """
                Save the time the input file enters the queue
            """
            
            flag1 = sys.argv[1]
            
            if temp_name not in task_mul:
                task_mul[temp_name] = [new_file]
                runtime_info = 'rt_enter '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info)
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
                
                
                
                # ts = time.time()
                # runtime_info = 'rt_exec '+ temp_name+ ' '+str(ts)
                # send_runtime_profile(runtime_info)
                # input_path = os.path.split(event.src_path)[0]
                # output_path = os.path.join(os.path.split(input_path)[0],'output')

                

                # dag_task = multiprocessing.Process(target=taskmodule.task, args=(filenames, input_path, output_path))
                # dag_task.start()
                # dag_task.join()
                # ts = time.time()
                # runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                # send_runtime_profile(runtime_info)


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
    
