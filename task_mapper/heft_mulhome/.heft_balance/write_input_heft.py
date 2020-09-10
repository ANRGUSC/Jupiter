#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
   This file generate the TGFF file required as an input of HEFT
"""
__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import sys
import pandas as pd
import json
import glob
import time
from create_input import init
import sys
from flask import Flask, request
import csv
import os

app = Flask(__name__)

'''
'''

network_info = []
execution_info = []


def get_global_info():
    """Get all information of profilers (network profilers, execution profilers)
    
    Returns:
        -   list: profiler_ip - IPs of network profilers
        -   list: exec_home_ip - IPs of execution profilers
        -   int:  num_nodes - number of nodes
        -   str:  MONGO_SVC_PORT - Mongo service port
        -   dict: network_map - mapping of node IPs and node names
        -   dict: node_list - node list
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
    tasks_info = open('dag.txt', "r")

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
    print("tasks: ", tasks)
    print("task order", task_order) #task_list
    print("super tasks", super_tasks)
    return tasks, task_order, super_tasks

def create_input_heft(tgff_file,num_nodes,network_info,execution_info,node_list,task_list,tasks):
    """Generate the TGFF file
    
    Args:
        - tgff_file (str): file of output TGFF file
        - num_nodes (int): number of nodes 
        - network_info (list): network profling information
        - execution_info (list): execution profiling information
        - node_list (list): list of nodes
        - task_list (list): (DAG) task list in the order of execution
        - tasks (list): DAG dictionary 
    """
    target = open(tgff_file, 'w')
    target.write('@TASK_GRAPH 0 {')
    target.write("\n")
    target.write('\tAPERIODIC')
    target.write("\n\n")

    task_map = ['t0_%d'%(i) for i in range(0,len(task_list))]
    task_ID_dict = dict(zip(task_list,range(0,len(task_list))))
    task_dict = dict(zip(task_list, task_map))
    computation_matrix =[]
    for i in range(0, len(task_list)):
        task_times = [0 for i in range(num_nodes)]
        computation_matrix.append(task_times)

    task_size = {}

    # Read format: Node ID, Task, Execution Time, Output size
    for row in execution_info:
        computation_matrix[task_ID_dict[row[1]]][node_ids[row[0]] - 1] = int(float(row[2])*10) 
        #100000
        task_size[row[1]] = row[3]

    for i in range(0,len(task_list)):
        line = "\tTASK %s\tTYPE %d \n" %(task_list[i], i)
        target.write(line)
    target.write("\n")

    # Need check
    v = 0
    keys = tasks.keys()
    for key in keys:
        for j in range(0, len(tasks[key])):
            #file size in Kbit is communication const
            comm_cost = int(float(task_size[key]))
            line = "\tARC a0_%d \tFROM %s TO %s \tTYPE %d" %(v,task_dict[key],task_dict.get(tasks[key][j]),comm_cost)
            v = v+1
            target.write(line)
            target.write("\n")
    target.write("\n")
    target.write('}')

    # OK
    target.write('\n@computation_cost 0 {\n')

    line = '# type version %s\n' %(' '.join(node_info[1:]))
    target.write(line)

    for i in range(0,len(task_list)):
        line='  %s    0\t%s\n'%(task_dict.get(task_list[i]),' '.join(str(x) for x in computation_matrix[i]))
        target.write(line)
    target.write('}')
    target.write('\n\n\n\n')

    target.write('\n@quadratic 0 {\n')
    target.write('# Source Destination a b c\n')


    #OK
    for row in network_info:
        line = '  %s\t%s\t%s\n'%(row[0],row[2],row[4])
        target.write(line)
    target.write('}')
    target.close()

    num_task, task_names, num_node, comp_cost, rate, data, quaratic_profile = init(tgff_file)
    print('Checking the written information')

    return

if __name__ == '__main__':

    NODE_NAMES = os.environ["NODE_NAMES"]
    node_info = NODE_NAMES.split(":")
    node_ids = {v:k for k,v in enumerate(node_info)}

    print('---------------------------------------------')
    print('\n Read task list from DAG file, Non-DAG info and global information \n')

    configuration_path='/heft/dag.txt'
    profiler_ip,exec_home_ip,num_nodes,network_map,node_list = get_global_info()
    tasks, task_order, super_tasks = get_taskmap()

    print('---------------------------------------------')
    print('\n Create input HEFT file \n')
    tgff_file='/heft/input.tgff'
    while True:
        if os.path.isfile('/heft/execution_log.txt') and os.path.isfile('/heft/network_log.txt'):
            with open('/heft/network_log.txt','r') as f:
                reader = csv.reader(f)
                network_info = list(reader)
            with open('/heft/execution_log.txt','r') as f:
                reader = csv.reader(f)
                execution_info = list(reader)
            # fix non-DAG tasks (temporary approach)
            new_execution = []
            for row in execution_info:
                if row[0]!='home':
                    new_execution.append(row)
                else:
                    print(row)
                    if row[1] in super_tasks:
                        for node in node_list:
                            new_execution.append([node,row[1],row[2],row[3]]) # to copy the home profiler data for the non dag task for each processor.
            create_input_heft(tgff_file,num_nodes,network_info,new_execution,node_list,task_order,tasks)
            break
        else:
            print('No available profiling information')
            time.sleep(10)
