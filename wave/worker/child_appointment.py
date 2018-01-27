"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pranav Sakulkar
 *      Pradipta Ghosh
 *      Jiatong Wang
 *      Aleksandra Knezevic
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

# -*- coding: utf-8 -*-

import json
import random
import re
import threading
import time
import os
import sys
import urllib
from urllib import parse
import shutil

import _thread
from flask import Flask, request
import requests
import datetime
from pymongo import MongoClient

app = Flask(__name__)

'''

'''

# Get ALL node info
node_count = 0
nodes = {}
for node_name, node_ip in zip(os.environ['ALL_NODES'].split(":"), os.environ['ALL_NODES_IPS'].split(":")):
    if node_name == "":
        continue
    nodes[node_name] = node_ip + ":48080"
    node_count +=  1
master_host = os.environ['HOME_IP'] + ":48080"
print("Nodes", nodes)

#
node_id = -1
node_name = ""
debug = True

# control relations between tasks
control_relation = {}

local_children = "local/local_children.txt"
local_mapping = "local/local_mapping.txt"
local_responsibility = "local/task_responsibility"

# lock for sync file operation
lock = threading.Lock()

kill_flag = False


@app.route('/assign_task')
def assign_task():
    try:
        task_name = request.args.get('task_name')
        write_file(local_responsibility + "/" + task_name, [], "w+")
        return "ok"
    except Exception:
        return "not ok"


@app.route('/kill_thread')
def kill_thread():
    global kill_flag
    kill_flag = True
    return "ok"


def init_folder():
    print("Trying to initialize folders here")
    try:
        if not os.path.exists("./local"):
            os.mkdir("./local")

        if not os.path.exists(local_children):
            write_file(local_children, [], "w+")

        if not os.path.exists(local_mapping):
            write_file(local_mapping, [], "w+")

        if not os.path.exists(local_responsibility):
            os.mkdir(local_responsibility)
        return "ok"
    except Exception:
        print("Init folder fialed: Why??")
        return "not ok"


@app.route('/recv_control')
def recv_control():
    try:
        control = request.args.get('control')
        items = re.split(r'#', control)

        to_be_write = []
        for _, item in enumerate(items):
            to_be_write.append(item.replace("__", "\t"))
            tmp = re.split(r"__", item)
            key = tmp[0]
            del tmp[0]
            control_relation[key] = tmp

        if not os.path.exists("./DAG"):
            os.mkdir("./DAG")

        write_file("DAG/parent_controller.txt", to_be_write, "a+")
    except Exception:
        return "not ok"
    return "ok"


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


def call_send_mapping(mapping, node):
    try:
        url = "http://" + master_host + "/recv_mapping"
        params = {'mapping': mapping, "node": node}
        params = parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        return "not ok"
    return res


# thread to watch directory: local/task_responsibility
def watcher():
    pre_time = time.time()

    tmp_mapping = ""
    while True:
        if kill_flag:
            break

        if not os.path.exists(local_responsibility):
            time.sleep(1)
            continue

        tasks = scan_dir(local_responsibility)
        output("Find tasks under task_responsibility: " + json.dumps(tasks))
        for _, task in enumerate(tasks):
            if task in control_relation.keys():
                controlled = control_relation[task]
                for _, t in enumerate(controlled):
                    todo_task = t + "\tTODO"
                    write_file(local_children, [todo_task], "a+")
                    output("Write content to local_children.txt: " + todo_task)

                write_file(local_mapping, [task], "a+")
                if tmp_mapping != "":
                    tmp_mapping = tmp_mapping + "#"
                tmp_mapping = tmp_mapping + task

                output("Write content to local_mapping.txt: " + task)
            else:
                write_file(local_mapping, [task], "a+")
                if tmp_mapping != "":
                    tmp_mapping = tmp_mapping + "#"
                tmp_mapping = tmp_mapping + task

                output("Write content to local_mapping.txt: " + task)

        shutil.rmtree(local_responsibility)
        os.mkdir(local_responsibility)

        if time.time() - pre_time >= 60:
            if tmp_mapping != "":
                res = call_send_mapping(tmp_mapping, node_name)
                if res != "ok":
                    output("Send mapping content to master failed");
                else:
                    tmp_mapping = ""

            pre_time = time.time()

        time.sleep(10)


# thread to assign todo task to nodes
def distribute():
    done_dict = set()
    while True:
        if kill_flag:
            break

        if not os.path.exists(local_children):
            time.sleep(1)
            continue

        lines = read_file(local_children)
        for line in lines:
            line = line.strip()
            if "TODO" in line:
                output("Find todo item: " + line)
                tmp_node_id = random.randint(1, node_count)
                while tmp_node_id == node_id and node_count > 1:
                    tmp_node_id = random.randint(1, node_count)

                assign_to_node = "node" + str(tmp_node_id)
                items = re.split(r'\t+', line)
                if items[0] in done_dict:
                    print(items[0], "already assigned")
                    continue

                print("Trying to assign", items[0], "to", assign_to_node)
                status = assign_task_to_remote(assign_to_node, items[0])
                if status == "ok":
                    output("Assign " + items[0] + " to " + assign_to_node + " successfully")
                    done_dict.add(items[0])
                else:
                    output("Assign " + items[0] + " to " + assign_to_node + " failed")

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


def output(msg):
    if debug:
        print(msg)

@app.route('/')
def hello_world():
    return 'Hello World!'

def get_resource_data():
    print("Startig resource profile collection thread")
    # Requsting resource profiler data using flask for its corresponding profiler node
    RP_PORT = 6100
    result = None
    while True:
        time.sleep(60)
        # print("Get resource profiler data from http://"+os.environ['PROFILER']+ ":" + str(RP_PORT))
        try:
            r = requests.get("http://"+os.environ['PROFILER']+":" + str(RP_PORT)+"/all")
            result = r.json()
            if len(result) != 0:
                break
        except Exception:
            print("Resource request failed. Will try again")

    data=json.dumps(result)
    print("Got profiler data from http://"+os.environ['PROFILER']+ ":" + str(RP_PORT))
    print("Resource profiles:", data)

def get_network_profile_data():
    # Collect the network profile from local MongoDB peer
    print('Collecting Netowrk Monitoring Data from MongoDB')
    NP_PORT = 6200
    client_mongo = MongoClient('mongodb://'+os.environ['PROFILER']+':'+str(NP_PORT)+'/')
    db = client_mongo.droplet_network_profiler
    print(db[os.environ['PROFILER']])

if __name__ == '__main__':
    node_name = os.environ['SELF_NAME']
    node_id = int(node_name.split("e")[-1])

    node_port = sys.argv[1]
    print("Node name:", node_name, "and id", node_id)
    print("Starting the main thread on port", node_port)

    while init_folder() != "ok": # Initialize the local folders
        pass

    # Get resource data
    _thread.start_new_thread(get_resource_data, ())

    # Get network profile data
    _thread.start_new_thread(get_network_profile_data, ())

    _thread.start_new_thread(watcher, ())
    _thread.start_new_thread(distribute, ())
    app.run(host='0.0.0.0', port=int(node_port))

