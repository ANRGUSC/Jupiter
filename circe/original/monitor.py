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
import multiprocessing
import time
import urllib
import urllib.request
import configparser
import numpy as np
from collections import defaultdict
import paho.mqtt.client as mqtt
import socket

global bottleneck
bottleneck = defaultdict(list)

def tic():
    return time.time()

def toc(t):
    texec = time.time() - t
    print('Execution time is:'+str(texec))
    return texec


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
        # print('***************************************************')
        # t = tic()
        # print("Sending monitor message", msg)
        url = "http://" + home_node_host_port + "/recv_monitor_data"
        params = {'msg': msg, "work_node": taskname}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        # txec = toc(t)
        # bottleneck['sendmsg'].append(txec)
        # print(np.mean(bottleneck['sendmsg']))
        # print('***************************************************')
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
    #     print('***************************************************')
    #     t = tic()
    #     print("Sending runtime message", msg)
        url = "http://" + home_node_host_port + "/recv_runtime_profile"
        # print(url)
        params = {'msg': msg, "work_node": taskname}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        # print(req)
        res = urllib.request.urlopen(req)
        # print(res)
        res = res.read()
        res = res.decode('utf-8')
        # print(res)
        # txec = toc(t)
        # bottleneck['sendruntime'].append(txec)
        # print(np.mean(bottleneck['sendruntime']))
        # print('***************************************************')
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
    #Keep retrying in case the containers are still building/booting up on
    #the child nodes.
    # print('***************************************************')
    # print('Transfer data')
    # t = tic()
    # print(IP)
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
    # txec = toc(t)
    # bottleneck['transfer'].append(txec)
    # print(np.mean(bottleneck['transfer']))
    # print('***************************************************')
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
    # print(msg)
    

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
    # print(msg)
    if TRANSFER==0:
        return multicast_data_scp
    return multicast_data_scp

# def demo_help(server,port,topic,msg):
#     # client = mqtt.Client()
#     # client.connect(server, port,300)
#     client.publish(topic, msg,qos=1)
    # client.disconnect()

def demo_help(server,port,topic,msg):
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()

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

            # print('***************************************************')
            
            
             
            print("Received file as output - %s." % event.src_path)
            # t = tic()

            #Runtime profiler (finished_time)
            
            """
                Save the time when a output file is available. This is taken as the end time of the task.
                The output time is stored in the file central_scheduler/runtime/droplet_runtime_output_(%node name)
            """
            # execution_end_time = datetime.datetime.utcnow()
            # pathrun = '/centralized_scheduler/runtime/'
            # runtime_file = os.path.join(pathrun,'droplet_runtime_output_' + node_name)

            # t1 = time.time()
            new_file = os.path.split(event.src_path)[-1]

            if '_' in new_file:
                temp_name = new_file.split('_')[0]
            else:
                temp_name = new_file.split('.')[0]
            # with open(runtime_file, 'a') as f:
            #     line = 'created_output, %s, %s, %s, %s\n' % (node_name, taskname, temp_name, execution_end_time)
            #     f.write(line)
            

            global files_out

            #based on flag2 decide whether to send one output to all children or different outputs to different children in
            #order given in the config file
            flag2 = sys.argv[2]

            #if you are sending the final output back to scheduler
            # print(time.time()-t1)
            # t1 = time.time()
            
            ts = time.time()
            print('====')
            print(sys.argv)
            print(flag2)
            print(taskname)
            if taskname == 'distribute':
                print('This is the distribution point')
                print(new_file)
                print(temp_name)
                appname = temp_name.split('-')[0]
                print(appname)
                source = event.src_path
                print(sys.argv)
                next_node = appname+'-task0'
                print(sys.argv.index(next_node))
                idx = sys.argv.index(next_node)
                IPaddr = sys.argv[idx+1]
                user = sys.argv[idx+2]
                password=sys.argv[idx+3]
                destination = os.path.join('/centralized_scheduler', 'input', new_file)
                transfer_data(IPaddr,user,password,source, destination)
            elif sys.argv[3] == 'home':
                if BOKEH == 1:
                    msg = taskname + " ends"
                    demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
                
                IPaddr = sys.argv[4]
                user = sys.argv[5]
                password=sys.argv[6]
                source = event.src_path
                destination = os.path.join('/output', new_file)
                transfer_data(IPaddr,user,password,source, destination)
                

            elif flag2 == 'true':

                if BOKEH == 1:
                    msg = taskname + " ends"
                    demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
                

                for i in range(3, len(sys.argv)-1,4):
                    IPaddr = sys.argv[i+1]
                    user = sys.argv[i+2]
                    password = sys.argv[i+3]
                    source = event.src_path
                    destination = os.path.join('/centralized_scheduler', 'input', new_file)
                    transfer_data(IPaddr,user,password,source, destination)

            else:
                num_child = (len(sys.argv) - 4) / 4
                files_out.append(new_file)

                print(num_child)
                print(files_out)

                if (len(files_out) == num_child):

                    if BOKEH == 1:
                        msg = taskname + " ends"
                        demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
                        

                    for i in range(3, len(sys.argv)-1,4):
                        myfile = files_out.pop(0)
                        event_path = os.path.join(''.join(os.path.split(event.src_path)[:-1]), myfile)
                        IPaddr = sys.argv[i+1]
                        user = sys.argv[i+2]
                        password = sys.argv[i+3]
                        source = event_path
                        destination = os.path.join('/centralized_scheduler','input', myfile)
                        transfer_data(IPaddr,user,password,source, destination)

                    files_out=[]

            # print(time.time()-t1)

            # txec = toc(t)
            # bottleneck['receiveoutput'].append(txec)
            # print(np.mean(bottleneck['receiveoutput']))
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

            # print('***************************************************')
            print("Received file as input - %s." % event.src_path)
            # t = tic()
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
                runtime_info = 'rt_enter '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info)
                if BOKEH == 1:
                    runtimebk = 'rt_enter '+ taskname+' '+ temp_name+ ' '+str(ts)
                    demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)

            flag1 = sys.argv[1]

            # t1 = time.time()
            if flag1 == "1":
    
                # Start msg
                ts = time.time()
                runtime_info = 'rt_exec '+ temp_name+ ' '+str(ts)
                send_runtime_profile(runtime_info)  
                if BOKEH == 1:
                    # msg = taskname + " starts "+str(ts)
                    runtimebk = 'rt_exec '+ taskname + ' '+temp_name+ ' '+str(ts)
                    demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
                    msg = taskname + " starts"
                    demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
                    
                inputfile=queue_mul.get()
                input_path = os.path.split(event.src_path)[0]
                output_path = os.path.join(os.path.split(input_path)[0],'output')
                dag_task = multiprocessing.Process(target=taskmodule.task, args=(inputfile, input_path, output_path))
                dag_task.start()
                dag_task.join()
                ts = time.time()
                if BOKEH == 1:
                    runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                    runtimebk = 'rt_finish '+ taskname+' '+temp_name+ ' '+str(ts)
                    send_runtime_profile(runtime_info)
                    demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
                # end msg
            else:

                filenames.append(queue_mul.get())
                if (len(filenames) == int(flag1)):

                    #start msg
                    ts = time.time()
                    runtime_info = 'rt_exec '+ temp_name+ ' '+str(ts)
                    send_runtime_profile(runtime_info)
                    
                        
                    if BOKEH == 1:
                        # msg = taskname + " starts "+str(ts)
                        runtimebk = 'rt_exec '+ taskname+' '+temp_name+ ' '+str(ts)
                        demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
                        msg = taskname + " starts"
                        demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)
                    input_path = os.path.split(event.src_path)[0]
                    output_path = os.path.join(os.path.split(input_path)[0],'output')

                    dag_task = multiprocessing.Process(target=taskmodule.task, args=(filenames, input_path, output_path))
                    dag_task.start()
                    dag_task.join()
                    filenames = []
                    ts = time.time()
                    if BOKEH == 1:
                        runtime_info = 'rt_finish '+ temp_name+ ' '+str(ts)
                        runtimebk = 'rt_finish '+ taskname+' '+temp_name+ ' '+str(ts)
                        demo_help(BOKEH_SERVER,BOKEH_PORT,taskname,runtimebk)
                        send_runtime_profile(runtime_info)
                    # end msg
            # print(time.time()-t1)
            # txec = toc(t)
            # bottleneck['receiveinput'].append(txec)
            # print(np.mean(bottleneck['receiveinput']))
            # print('***************************************************')

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

    global FLASK_SVC, MONGO_PORT, username,password,ssh_port, num_retries, queue_mul

    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT  = int(config['PORT']['MONGO_DOCKER'])
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])


    global taskmap, taskname, taskmodule, filenames,files_out, node_name, home_node_host_port, all_nodes, all_nodes_ips

    configs = json.load(open('/centralized_scheduler/config.json'))
    taskmap = configs["taskname_map"][sys.argv[len(sys.argv)-1]]
    taskname = taskmap[0]
    # print(taskname)
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

    print('Bokeh information')
    print(BOKEH_SERVER)
    print(BOKEH_PORT)
    print(BOKEH)

    # global client
    # client = mqtt.Client()
    # client.connect(BOKEH_SERVER, BOKEH_PORT,300)


    print('Taskmapping information')
    print(taskmap[1])
    if taskmap[1] == True:
        print('Monitor INPUT & OUTPUT')
        queue_mul=multiprocessing.Queue()

        #monitor INPUT as another process
        w=Watcher()
        w.start()

        #monitor OUTPUT in this process
        w1=Watcher1()
        w1.run()
    else:
        print('Task Mapping information')
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
    
