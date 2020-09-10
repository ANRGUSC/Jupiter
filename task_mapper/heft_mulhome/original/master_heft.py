#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
   This file implements HEFT code in the kubernettes system.
"""
__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import heft_dup
import os
import time
from flask import Flask, request
import json
from random import randint
import configparser
from os import path
import paho.mqtt.client as mqtt

app = Flask(__name__)

def read_file(file_name):
    """Read file content to a list
    
    Args:
        file_name (str): path of file
    
    Returns:
        list: file content 
    """
    file_contents = []
    file = open(file_name)
    line = file.readline()
    while line:
        file_contents.append(line)
        line = file.readline()
    file.close()
    return file_contents
    


assignments = {}

def return_assignment():
    """Return the current assignments have been done until the request time
    
    Returns:
        json: assignments of tasks and corresponding nodes
    """
    print("Recieved request for current mapping. Current mappings done:", len(assignments))
    print(assignments)
    if len(assignments) >= MAX_TASK_NUMBER:
        return json.dumps(assignments)
    else:
        return json.dumps(dict())
app.add_url_rule('/', 'return_assignment', return_assignment)

def get_global_info():
    """Get global information (network profilers and execution profilers)
    
    Returns:
        - str: profiler_ip - IPs of network profilers
        - str: exec_home_ip - IP of execution profiler
        - int: num_nodes - number of nodes
        - dict: network_map - mapping between node IPs and node names
        - list: node_list - list of nodes
    """
    profiler_ip = os.environ['PROFILERS'].split(' ')
    profiler_ip = [info.split(":") for info in profiler_ip]
    exec_home_ip = os.environ['EXECUTION_HOME_IP']
    num_nodes = len(profiler_ip)
    node_list = [info[0] for info in profiler_ip]
    node_IP = [info[1] for info in profiler_ip]
    network_map = dict(zip(node_IP, node_list))
    return profiler_ip,exec_home_ip,num_nodes,network_map,node_list

def get_taskmap():
    """Get the task map from ``config.json`` and ``dag.txt`` files.
    
    Returns:
        - dict: tasks - DAG dictionary
        - list: task_order - (DAG) task list in the order of execution
        - list: super_tasks 
        - list: non_tasks - tasks not belong to DAG
    """
    configs = json.load(open('/heft/config.json'))
    task_map = configs['taskname_map']
    execution_map = configs['exec_profiler']
    tasks_info = open('/heft/dag.txt', "r")

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

def old_demo_help(server,port,topic,msg):
    client = mqtt.Client()
    client.connect(server, port,60)
    client.publish(topic, msg,qos=1)
    client.disconnect()
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

def main():
    """
        - Load all the confuguration
        - Check whether the input TGFF file has been generated
        - Assign random master and slaves for now
    """
    print('Starting to run HEFT mapping')
    starting_time = time.time()

    global node_info, MAX_TASK_NUMBER, FLASK_PORT, MONGO_SVC_PORT, assignments

    NODE_NAMES = os.environ["NODE_NAMES"]
    node_info = NODE_NAMES.split(":")

    application = read_file("dag.txt")
    MAX_TASK_NUMBER = int(application[0])

    ##
    ## Load all the confuguration
    ##
    HERE     = path.abspath(path.dirname(__file__)) + "/"
    INI_PATH = HERE + 'jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    FLASK_PORT = int(config['PORT']['FLASK_DOCKER'])
    MONGO_SVC_PORT = config['PORT']['MONGO_SVC']

    tgff_file = '/heft/input.tgff'
    output_file = '/heft/input_to_CIRCE.txt'
    tasks, task_order, super_tasks, non_tasks = get_taskmap()
    configuration_path='/heft/dag.txt'
    profiler_ip,exec_home_ip,num_nodes,network_map,node_list = get_global_info()

    global BOKEH_SERVER, BOKEH_PORT, BOKEH, app_name,app_option
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])
    app_name = os.environ['APP_NAME']
    app_option = os.environ['APP_OPTION']

    
    while True:
        if os.path.isfile(tgff_file):
            print(' File TGFF was generated!!!')
            heft_scheduler = heft_dup.HEFT(tgff_file)
            print('Start the HEFT scheduler')
            heft_scheduler.run()
            heft_scheduler.display_result(0)
            heft_scheduler.run_dup_split()
            print('Output of HEFT scheduler')
            heft_scheduler.display_result(1)
            heft_scheduler.output_file(output_file)
            assignments = heft_scheduler.output_assignments()
            print('Assign random master and slaves')
            for i in range(0,len(non_tasks)):
                assignments[non_tasks[i]] = node_info[randint(1,num_nodes)] 
            #heft_scheduler.display_result(1)
            t = time.time()
            if len(assignments) == MAX_TASK_NUMBER:
                print('Successfully finish HEFT mapping ')
                end_time = time.time()
                deploy_time = end_time - starting_time
                print('Time to finish HEFT mapping '+ str(deploy_time))

            if BOKEH==3:
                topic = 'mappinglatency_%s'%(app_option)
                msg = 'mappinglatency originalheft %s %f \n' %(app_name,deploy_time)
                demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
        
            if BOKEH == 1:
                assgn = ' '.join('{}:{}:{}'.format(key, val,t) for key, val in assignments.items())
                msg = "mappings "+ assgn
                old_demo_help(BOKEH_SERVER,BOKEH_PORT,"JUPITER",msg)

            break;
        else:
            print('No input TGFF file found!')
            time.sleep(5)

    app.run(host='0.0.0.0', port = int(FLASK_PORT)) # TODO?

if __name__ == '__main__':
    main()
