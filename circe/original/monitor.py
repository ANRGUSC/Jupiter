#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on every node of the system.
"""

__author__ = "Aleksandra Knezevic,Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,  Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

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
import time
import urllib
import urllib.request
import configparser
import numpy as np
from collections import defaultdict
import paho.mqtt.client as mqtt
import socket
import pyinotify
from collections import Counter
import _thread
import threading



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
        url = "http://" + home_node_host_port + "/recv_monitor_data"
        params = {'msg': msg, "work_node": taskname}
        params = urllib.parse.urlencode(params)
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
        url = "http://" + home_node_host_port + "/recv_runtime_profile"
        params = {'msg': msg, "work_node": taskname}
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

def transfer_data_scp(ID,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        ID (str): destination ID
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
            nodeIP = combined_ip_map[ID]
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, nodeIP, destination)
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
    
    if TRANSFER == 0:
        return transfer_data_scp(ID,user,pword,source, destination)

    return transfer_data_scp(ID,user,pword,source, destination) #default

def transfer_multicast_data_scp(ID_list,user_list,pword_list,source, destination):
    """Transfer data using SCP to multiple nodes
    
    Args:
        ID_list (str): destination ID list
        user_list (str): username list
        pword_list (str): password list
        source (str): source file path 
        destination (str): destination file path
    """
    for idx in range(len(ID_list)): 
        _thread.start_new_thread(transfer_data_scp,(ID_list[idx],user_list[idx],pword_list[idx],source, destination,))

def transfer_multicast_data(ID_list,user_list,pword_list,source, destination):
    """Transfer data with given parameters
    
    Args:
        ID_list (str): destination ID list 
        user (str): destination username
        pword (str): destination password
        source (str): source file path
        destination (str): destination file path
    """
    for idx in range(len(ID_list)):
        msg = 'Transfer to IP: %s , username: %s , password: %s, source path: %s , destination path: %s'%(ID_list[idx],user_list[idx],pword_list[idx],source, destination)
    if TRANSFER==0:
        print('Multicast all the files')
        transfer_multicast_data_scp(ID_list,user_list,pword_list,source, destination)
    

def demo_help(server,port,topic,msg):
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()

class Handler1(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        print("Received file as output - %s." % event.pathname)
        
        """
            Save the time when a output file is available. This is taken as the end time of the task.
            The output time is stored in the file central_scheduler/runtime/droplet_runtime_output_(%node name)
        """
        new_file = os.path.split(event.pathname)[-1]

        if '_' in new_file:
            temp_name = new_file.split('_')[0]
        else:
            temp_name = new_file.split('.')[0]
        global files_out

        #based on flag2 decide whether to send one output to all children or different outputs to different children in
        #order given in the config file
        flag2 = sys.argv[2]
        ts = time.time()
        if taskname == 'distribute':
            print('This is the distribution point')
            ts = time.time()
            runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
            send_runtime_profile(runtime_info)
            if BOKEH == 1:
                runtimebk = 'rt_finish '+ taskname+' '+temp_name+ ' '+str(ts)
                demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
            appname = temp_name.split('-')[0]
            source = event.pathname
            next_node = appname+'-task0'
            idx = sys.argv.index(next_node)
            next_task = sys.argv[idx]
            user = sys.argv[idx+2]
            password=sys.argv[idx+3]
            destination = os.path.join('/centralized_scheduler', 'input', new_file)
            transfer_data(next_task,user,password,source, destination)
        elif sys.argv[3] == 'home':
            print('Next node is home')
            ts = time.time()
            runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
            send_runtime_profile(runtime_info)
            if BOKEH == 1:
                runtimebk = 'rt_finish '+ taskname+' '+temp_name+ ' '+str(ts)
                demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)

            if BOKEH == 0:
                msg = taskname + " ends"
                demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
            
            user = sys.argv[5]
            password=sys.argv[6]
            source = event.pathname
            destination = os.path.join('/output', new_file)
            transfer_data('home',user,password,source, destination)
            

        elif flag2 == 'true':
            print('Flag is true -- using multicast instead')
            ts = time.time()
            runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
            send_runtime_profile(runtime_info)
            if BOKEH == 1:
                runtimebk = 'rt_finish '+ taskname+' '+temp_name+ ' '+str(ts)
                demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)

            if BOKEH == 0:
                msg = taskname + " ends"
                demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
            
            # Using unicast 
            # for i in range(3, len(sys.argv)-1,4):
            #     cur_task = sys.argv[i]
            #     # IPaddr = sys.argv[i+1]
            #     user = sys.argv[i+2]
            #     password = sys.argv[i+3]
            #     source = event.pathname
            #     destination = os.path.join('/centralized_scheduler', 'input', new_file)
            #     transfer_data(cur_task,user,password,source, destination)
            
            # Using multicast
            cur_tasks =[]
            users = []
            passwords = []
            source = event.pathname
            destination = os.path.join('/centralized_scheduler', 'input', new_file)

            for i in range(3, len(sys.argv)-1,4):
                cur_tasks.append(sys.argv[i])
                users.append(sys.argv[i+2])
                passwords.append(sys.argv[i+3])
                
            transfer_multicast_data(cur_tasks,users,passwords,source, destination)
        else:
            print('Flag is false -- using unicast')
            num_child = (len(sys.argv) - 4) / 4
            files_out.append(new_file)
            if (len(files_out) == num_child):
                # send runtime profiling information
                ts = time.time()
                runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info)
                if BOKEH == 1:
                    runtimebk = 'rt_finish '+ taskname+' '+temp_name+ ' '+str(ts)
                    demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
                if BOKEH == 0:
                    msg = taskname + " ends"
                    demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
                    
                for i in range(3, len(sys.argv)-1,4):
                    myfile = files_out.pop(0)
                    event_path = os.path.join(''.join(os.path.split(event.pathname)[:-1]), myfile)
                    cur_task = sys.argv[i]
                    user = sys.argv[i+2]
                    password = sys.argv[i+3]
                    source = event_path
                    destination = os.path.join('/centralized_scheduler','input', myfile)
                    transfer_data(cur_task,user,password,source, destination)

                files_out=[]



class Handler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """

    def process_IN_CLOSE_WRITE(self, event):
        print("Received file as input - %s." % event.pathname)

        new_file = os.path.split(event.pathname)[-1]


        """
            Save the time when an input file is available. This is taken as the start time of the task.
            The output time is stored in the file central_scheduler/runtime/droplet_runtime_input_(%node name)
        """
        
        new_file = os.path.split(event.pathname)[-1]
        if '_' in new_file:
            temp_name = new_file.split('_')[0]
        else:
            temp_name = new_file.split('.')[0]


        queue_mul.put(new_file)
        
        ts = time.time()
        if RUNTIME == 1:
            s = "{:<10} {:<10} {:<10} {:<10} \n".format(node_name,transfer_type,event.pathname,ts)
            runtime_receiver_log.write(s)
            runtime_receiver_log.flush()

        """
            Save the time the input file enters the queue
        """
        filename = new_file
        global filenames

        if len(filenames) == 0:
            runtime_info = 'rt_enter '+ temp_name+ ' '+str(ts)
            send_runtime_profile(runtime_info)
            if BOKEH == 1:
                runtimebk = 'rt_enter '+ taskname+' '+ temp_name+ ' '+str(ts)
                demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
        flag1 = sys.argv[1]
        if flag1 == "1":
            ts = time.time()
            runtime_info = 'rt_exec '+ temp_name+ ' '+str(ts)
            send_runtime_profile(runtime_info)  
            if BOKEH == 1:
                runtimebk = 'rt_exec '+ taskname + ' '+temp_name+ ' '+str(ts)
                demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
            if BOKEH == 0:
                msg = taskname + " starts"
                demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)                
            inputfile=queue_mul.get()
            input_path = os.path.split(event.pathname)[0]
            output_path = os.path.join(os.path.split(input_path)[0],'output')
            dag_task = multiprocessing.Process(target=taskmodule.task, args=(inputfile, input_path, output_path))
            dag_task.start()
            dag_task.join()
           
        else:
            filenames.append(queue_mul.get())
            if (len(filenames) == int(flag1)):
                ts = time.time()
                runtime_info = 'rt_exec '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info)           
                if BOKEH == 1:
                    runtimebk = 'rt_exec '+ taskname+' '+temp_name+ ' '+str(ts)
                    demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
                if BOKEH == 0:
                    msg = taskname + " starts"
                    demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
                input_path = os.path.split(event.pathname)[0]
                output_path = os.path.join(os.path.split(input_path)[0],'output')
                dag_task = multiprocessing.Process(target=taskmodule.task, args=(filenames, input_path, output_path))
                dag_task.start()
                dag_task.join()
                filenames = []



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

    global FLASK_SVC, FLASK_DOCKER, MONGO_PORT, username,password,ssh_port, num_retries, queue_mul

    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT  = int(config['PORT']['MONGO_DOCKER'])
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])


    global taskmap, taskname, taskmodule, filenames,files_out, node_name, home_node_host_port, all_nodes, all_nodes_ips

    configs = json.load(open('/centralized_scheduler/config.json'))
    taskmap = configs["taskname_map"][sys.argv[len(sys.argv)-1]]
    taskname = taskmap[0]
    if taskmap[1] == True:
        taskmodule = __import__(taskname)

    #target port for SSHing into a container
    filenames=[]
    files_out=[]
    node_name = os.environ['NODE_NAME']
    home_node_host_port = os.environ['HOME_NODE'] + ":" + str(FLASK_SVC)

    all_nodes = os.environ["ALL_NODES"].split(":")
    all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":")

    
    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

    global combined_ip_map 
    combined_ip_map = dict()
    for i in range(3, len(sys.argv)-1,4):
        node = sys.argv[i]
        IPaddr = sys.argv[i+1]
        user = sys.argv[i+2]
        password = sys.argv[i+3]
        combined_ip_map[node] = IPaddr

    if taskmap[1] == True:
        queue_mul=multiprocessing.Queue()


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
    else:
        print('Task Mapping information')
        path_src = "/centralized_scheduler/" + taskname
        args = ' '.join(str(x) for x in taskmap[2:])

        if os.path.isfile(path_src + ".py"):
            cmd = "python3 -u " + path_src + ".py " + args          
        else:
            cmd = "sh " + path_src + ".sh " + args
        os.system(cmd)

if __name__ == '__main__':
    main()
    
