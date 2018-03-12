import heft_dup
import os
import time
from flask import Flask, request
import json
from random import randint

# from node_info import *
print("starting the main thread on port")

app = Flask(__name__)

'''
'''

"""
This module is a test module. You should take three steps:
1. Instantiating a HEFT objects.
2. Calling run() method.
3. Calling display_result() method.
"""

MAX_TASK_NUMBER = 41 # Total number of tasks in the DAG ## TODO : Automate
assignments = {}

@app.route('/')
def return_assignment():
    print("Recieved request for current mapping. Current mappings done:", len(assignments))
    print(assignments)
    if len(assignments) == MAX_TASK_NUMBER:
        return json.dumps(assignments)
    else:
        return json.dumps(dict())

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

if __name__ == '__main__':
    tgff_file = '/heft/input.tgff'
    output_file = '/heft/input_to_CIRCE.txt'
    tasks, task_order, super_tasks, non_tasks = get_taskmap()
    configuration_path='/heft/dag.txt'
    profiler_ip,exec_home_ip,num_nodes,network_map,node_list = get_global_info()
    while True:
        if os.path.isfile(tgff_file):
            heft_scheduler = heft_dup.HEFT(tgff_file)
            heft_scheduler.run()
            heft_scheduler.output_file(output_file)
            assignments = heft_scheduler.output_assignments()
            print('Assign random master and slaves')
            for i in range(0,len(non_tasks)):
                assignments[non_tasks[i]] = 'node'+ str(randint(1,num_nodes)) 
            heft_scheduler.display_result()
            print(assignments)
            break;
        else:
            print('No input TGFF file found!')
            time.sleep(15)

    app.run(host='0.0.0.0', port=8888)