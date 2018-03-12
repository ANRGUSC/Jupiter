"""
 ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 **     contributor: Quynh Nguyen, Aleksandra Knezevic, Bhaskar Krishnamachari
 **     Read license file in main directory for more details
"""

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
# from node_info import *
print("starting the main thread on port")

app = Flask(__name__)

'''
'''

network_info = []
execution_info = []
debug = True


def output(msg):
    if debug:
        print(msg)

def get_global_info():
    profiler_ip = os.environ['PROFILERS'].split(' ')
    profiler_ip = [info.split(":") for info in profiler_ip]
    exec_home_ip = os.environ['EXECUTION_HOME_IP']
    num_nodes = len(profiler_ip)
    node_list = [info[0] for info in profiler_ip]
    node_IP = [info[1] for info in profiler_ip]
    network_map = dict(zip(node_IP, node_list))
    return profiler_ip,exec_home_ip,num_nodes,network_map,node_list

def get_taskmap():
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

    target = open(tgff_file, 'w')
    target.write('@TASK_GRAPH 0 {')
    target.write("\n")
    target.write('\tAPERIODIC')
    target.write("\n\n")

    output(task_list)
    task_map = ['t0_%d'%(i) for i in range(0,len(task_list))]
    task_ID_dict = dict(zip(task_list,range(0,len(task_list))))
    task_dict = dict(zip(task_list, task_map))
    output(task_dict)
    output(task_ID_dict)

    computation_matrix =[]
    for i in range(0, len(task_list)):
        task_times = []
        computation_matrix.append(task_times)

    task_size = {}

    # Read format: Node ID, Task, Execution Time, Output size
    for row in execution_info:
        computation_matrix[task_ID_dict[row[1]]].append(int(float(row[2])*10)) #100000
        task_size[row[1]]=row[3]
    output(task_size)
    output(computation_matrix)

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

    line = '# type version %s\n' %(' '.join(node_list))
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
    output('Checking the written information')
    output(num_task)
    # output(num_processor)
    output(comp_cost)
    output(rate)
    output(data)
    output(quaratic_profile)

    return

if __name__ == '__main__':


    print('---------------------------------------------')
    print('\n Read task list from DAG file, Non-DAG info and global information \n')

    configuration_path='/heft/dag.txt'
    profiler_ip,exec_home_ip,num_nodes,network_map,node_list = get_global_info()
    # output(profiler_ip)
    # output(exec_home_ip)
    # output("Num nodes :" + str(num_nodes))
    # output(network_map)
    # output(node_list)
    tasks, task_order, super_tasks = get_taskmap()

    print('---------------------------------------------')
    print('\n Create input HEFT file \n')
    tgff_file='/heft/input.tgff'
    while True:
        if os.path.isfile('/heft/execution_log.txt') and os.path.isfile('/heft/network_log.txt'):
            with open('/heft/network_log.txt','r') as f:
                reader = csv.reader(f)
                network_info = list(reader)
                #output(network_info)
            with open('/heft/execution_log.txt','r') as f:
                reader = csv.reader(f)
                execution_info = list(reader)
                #output(execution_info)
            # fix non-DAG tasks (temporary approach)
            new_execution = []
            for row in execution_info:
                if row[0]!='home':
                    new_execution.append(row)
                else:
                    print(row)
                    if row[1] in super_tasks:
                        for node in node_list:
                            new_execution.append([node,row[1],row[2],row[3]])
            #print(new_execution)
            create_input_heft(tgff_file,num_nodes,network_info,new_execution,node_list,task_order,tasks)
            break
        else:
            print('No available profiling information')
            time.sleep(10)
