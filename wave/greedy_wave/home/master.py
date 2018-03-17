"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pranav Sakulkar
 *      Jiatong Wang
 *      Pradipta Ghosh
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

# -*- coding: utf-8 -*-

import re
import threading
import os
import urllib
from urllib import parse
import json
import sys
import _thread
import time
from flask import Flask, request
import configparser
from os import path

##
## Load all the confuguration
##
INI_PATH = '/jupiter_config.ini'

config = configparser.ConfigParser()
config.read(INI_PATH)

FLASK_PORT = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC  = int(config['PORT']['FLASK_SVC'])
MONGO_SVC  = int(config['PORT']['MONGO_SVC'])

# from node_info import *
print("starting the main thread on port")

app = Flask(__name__)

'''
'''

# Get ALL node info
node_count = 0
nodes = {}
docker_ip2node_name = {}
task_assign_summary = []

for node_name, node_ip in zip(os.environ['ALL_NODES'].split(':'), os.environ['ALL_NODES_IPS'].split(':')):
    if node_name == "":
        continue
    nodes[node_name] = node_ip + ":" + str(FLASK_SVC)
    node_count += 1
master_host = os.environ['HOME_IP'] + ":" + str(FLASK_SVC)
print("Nodes", nodes)

#
node_id = -1
node_name = ""
debug = True

# control relations between tasks
control_relation = {}
# task's children tasks
children = {}
# task's parent tasks
parents = {}
# running tasks in node in at the beginning
init_tasks = {}

local_children = "local/local_children.txt"
local_mapping = "local/local_mapping.txt"
local_responsibility = "local/task_responsibility"

# lock for sync file operation
lock = threading.Lock()
# get all lines in a file
def read_file(file_name):
    lock.acquire()
    file_contents = []
    file = open(file_name)
    line = file.readline()
    while line:
        file_contents.append(line)
        line = file.readline()
    file.close()
    lock.release()
    return file_contents


assigned_tasks = {}

application = read_file("DAG/DAG_application.txt")
MAX_TASK_NUMBER = int(application[0])  # Total number of tasks in the DAG 
print("Max task number ", MAX_TASK_NUMBER)
del application[0]

assignments = {}


@app.route('/recv_task_assign_info')
def recv_task_assign_info():
    assign = request.args.get('assign')
    task_assign_summary.append(assign)
    print("Task assign summary: " + json.dumps(task_assign_summary))
    return 'ok'


@app.route('/recv_node_name2docker_ip')
def recv_node_name2docker_ip():
    mapping = request.args.get('mapping')
    items = re.split(r':', mapping)
    docker_ip2node_name[items[1]] = items[0]
    return 'ok'


@app.route('/send_node_name2docker_ip')
def send_node_name2docker_ip():
    return json.dumps(docker_ip2node_name)


@app.route('/recv_mapping')
def recv_mapping():
    try:
        node = request.args.get('node')
        mapping = request.args.get("mapping")

        to_be_write = []
        items = re.split(r'#', mapping)
        for _, p in enumerate(items):
            p = p.strip()
            assigned_tasks[p] = 1
            assignments[p] = node
            to_be_write.append(p + '\t' + node)

        if not os.path.exists("./local"):
            os.mkdir("./local")

        write_file("local/input_to_CIRCE.txt", to_be_write, "a+")
    except Exception:
        return "not ok"
    return "ok"


@app.route('/')
def return_assignment():
    print("Recieved request for current mapping. Current mappings done:", len(assignments))
    print(assignments)
    if len(assignments) == MAX_TASK_NUMBER:
        return json.dumps(assignments)
    else:
        return json.dumps(dict())


def assign_task_to_remote(assigned_node, task_name):
    try:
        url = "http://" + nodes[assigned_node] + "/assign_task"
        params = {'task_name': task_name}
        params = parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception:
        return "not ok"
    return res


def call_recv_control(assigned_node, control):
    try:
        url = "http://" + nodes[assigned_node] + "/recv_control"
        print(url)
        params = {'control': control}
        params = parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception:
        return "not ok"
    return res


def call_kill_thread(node):
    try:
        url = "http://" + nodes[node] + "/kill_thread"
        req = urllib.request.Request(url=url)
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception:
        return "not ok"
    return res


# thread to watch directory: local/task_responsibility
def init_thread():
    # init folder and file under local for all nodes

    # send control info to all nodes
    line = ""
    for key in control_relation:
        controlled = control_relation[key]
        if line != "":
            line = line + "#"
        line = line + key
        for _, item in enumerate(controlled):
            line = line + "__" + item
    for node in nodes:
        res = call_recv_control(node, line)
        if res != "ok":
            output("Send control info to node %s failed" % node)

    # assign task init task to nodes
    for key in init_tasks:
        tasks = init_tasks[key]
        for _, task in enumerate(tasks):
            res = assign_task_to_remote(key, task)
            if res != "ok":
                output("Assign task %s to node %s failed" % (task, node))


def monitor_task_status():
    killed = 0
    while True:
        if len(assigned_tasks) == MAX_TASK_NUMBER:
            print("All task allocations are done! Great News!")
            for node in nodes:
                res = call_kill_thread(node)
                if res != "ok":
                    output("Kill node thread failed: " + str(node))
                else:
                    killed += 1
        if killed == MAX_TASK_NUMBER:
            break
        time.sleep(10)


def scan_dir(directory):
    tasks = []
    for file_name in os.listdir(directory):
        tasks.append(file_name)
    return tasks


def create_file():
    pass


def write_file(file_name, content, mode):
    lock.acquire()
    file = open(file_name, mode)
    for line in content:
        file.write(line + "\n")
    file.close()
    lock.release()


def init_task_topology():
    input_nodes = read_file("DAG/input_node.txt")
    del input_nodes[0]
    for line in input_nodes:
        line = line.strip()
        # items = re.split(r'\t+', line)
        items = line.split()
        task = items[0]

        for node in items[1:]:
            if node in init_tasks.keys():
                init_tasks[node].append(task)
            else:
                init_tasks[node] = [task]

    print("init_tasks" ,init_tasks)

    # application = read_file("DAG/DAG_application.txt")
    # MAX_TASK_NUMBER = int(application[0])
    # del application[0]
    for line in application:
        line = line.strip()
        # items = re.split(r'\t+', line)
        items = line.split()

        parent = items[0]
        if parent == items[3] or items[3] == "home":
            continue

        children[parent] = items[3:]

        print(parent)
        print(items[3:])

        for child in items[3:]:
            if child in parents.keys():
                parents[child].append(parent)
            else:
                parents[child] = [parent]

    print("parents" ,parents)

    for key in parents:
        parent = parents[key]
        if len(parent) == 1:
            if parent[0] in control_relation:
                control_relation[parent[0]].append(key)
            else:
                control_relation[parent[0]] = [key]
        if len(parent) > 1:
            flag = False
            for p in parent:
                if p in control_relation:
                    control_relation[p].append(key)
                    flag = True
                    break
            if not flag:
                control_relation[parent[0]] = [key]

    to_be_write = []
    for key in control_relation:
        controlled = control_relation[key]
        line = key
        for child in controlled:
            line = line + '\t' + child
        to_be_write.append(line)

    print("control_relation" ,control_relation)
    write_file("DAG/parent_controller.txt", to_be_write, "a+")





def output(msg):
    if debug:
        print(msg)


if __name__ == '__main__':
    # node_port = FLASK_PORT
    print("starting the main thread on port", FLASK_PORT)

    init_task_topology()
    _thread.start_new_thread(init_thread, ())
    _thread.start_new_thread(monitor_task_status, ())
    app.run(host='0.0.0.0', port=int(FLASK_PORT))

