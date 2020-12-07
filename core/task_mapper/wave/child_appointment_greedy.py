"""
.. note:: This is the main script to run in every worker node for greedy WAVE.
"""
__author__ = "Quynh Nguyen, Pranav Sakulkar,  Jiatong Wang, Pradipta Ghosh,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

import json
import re
import threading
import time
import os
import sys
import urllib
import shutil
import _thread
from flask import Flask, request
import requests
from pymongo import MongoClient
import configparser
from os import path
from functools import wraps
import multiprocessing
from multiprocessing import Process, Manager
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paho.mqtt.client as mqtt
import socket
import logging

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

"""Paths specific to container (see Dockerfile)"""
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
WAVE_FILES_DIR = '/jupiter/'


app = Flask(__name__)



def init_task_topology():
    """
        - Read ``DAG/input_node.txt``, get inital task information for each node
        - Read ``DAG/DAG_application.txt``, get parent list of child tasks
        - Create the DAG
        - Write control relations to ``DAG/parent_controller.txt``
    """

    for line in application:
        line = line.strip()
        items = line.split()

        parent = items[0]
        if parent == items[3] or items[3] == "home":
            continue

        children[parent] = items[3:]
        for child in items[3:]:
            if child in parents.keys():
                parents[child].append(parent)
            else:
                parents[child] = [parent]

    for key, value in sorted(parents.items()):
        parent = value
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
    logging.debug('----------- Control relation')
    logging.debug("control_relation" ,control_relation)

def assign_task():
    """Request assigned node for a specific task, write task assignment in local file at ``local_responsibility/task_name``.

    Raises:
        Exception: ``ok`` if successful, ``not ok`` if either the request or the writing is failed
    """
    try:

        task_name = request.args.get('task_name')

        local_mapping[task_name] = False
        res = call_send_mapping(task_name, node_name)

        if len(control_relation[task_name])>0:
            for task in control_relation[task_name]:
                if task not in local_children.keys():
                    local_children[task] = False
                    write_file(local_responsibility + "/" + task, 'TODO', "w+")
        else:
            logging.debug('No children tasks for this task')

        return "ok"
    except Exception as e:
        logging.debug(e)
        return "not ok"
app.add_url_rule('/assign_task', 'assign_task', assign_task)

def assign_task_to_remote(assigned_node, task_name):
    """Assign task to remote node

    Args:
        - assigned_node (str): Node to be assigned
        - task_name (str): task name

    Raises:
        Exception: request if successful, ``not ok`` if failed
    """
    try:
        logging.debug('Assign children task to the remote node')
        url = "http://" + nodes[assigned_node] + "/assign_task"
        params = {'task_name': task_name}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception:
        return "not ok"
    return res

def write_file(file_name, content, mode):
    """Write the content to file

    Args:
        - file_name (str): file path
        - content (str): content to be written
        - mode (str): write mode
    """
    file = open(file_name, mode)
    for line in content:
        file.write(line + "\n")
    file.close()

def call_send_mapping(mapping, node):
    """
    - A function that used for intermediate data transfer.
    - Return mapping information for specific node.

    Args:
        - mapping (dict): mapping information (task-assigned node)
        - node (str): node name

    Raises:
        Exception: request if successful, ``not ok`` if failed
    """
    try:
        logging.debug('Announce the mapping to the master host')
        url = "http://" + master_host + "/recv_mapping"
        params = {'mapping': mapping, "node": node}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        local_mapping[mapping] = True
    except Exception as e:
        return "Announce the mapping to the master host failed"
    return res

class Watcher:
    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'task_responsibility')

    def __init__(self):
        self.observer = Observer()

    def run(self):
        """
        Monitoring ``INPUT`` folder for the incoming files.

        At the moment you have to manually place input files into the ``INPUT`` folder (which is under ``centralized_scheduler_with_task_profiler``):

            .. code-block:: bash

                mv 1botnet.ipsum input/

        Once the file is there, it sends the file to the node performing the first task.
        """

        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()

class Handler(FileSystemEventHandler):
    """
        Handling the event when there is a new file generated in ``INPUT`` folder
    """

    @staticmethod
    def on_any_event(event):
        """
        Whenever there is a new input file in ``INPUT`` folder, the function:

        - Log the time the file is created

        - Start the connection to the first scheduled node

        - Copy the newly created file to the ``INPUT`` folder of the first scheduled node

        Args:
            event (FileSystemEventHandler): monitored event
        """

        if event.is_directory:
            return None

        elif event.event_type == 'created':

            logging.debug("Received file as input - %s." % event.src_path)
            new_task = os.path.split(event.src_path)[-1]
            _thread.start_new_thread(assign_children_task,(new_task,))


def assign_children_task(children_task):
    logging.debug('Starting assigning process for the children task')
    while True:
        if is_network_profile_data_ready and is_resource_data_ready:
            break
        else:
            logging.debug("Waiting for the profiler data")
            time.sleep(100)
    res = False
    if 'app' in children_task:
        appname = children_task.split('-')[0]
        sample_file = '/'+appname+'-1botnet.ipsum'
    else:
        sample_file = '/1botnet.ipsum'
    sample_size = cal_file_size(sample_file)
    assign_to_node = get_most_suitable_node(sample_size)
    if not assign_to_node:
        logging.debug("No suitable node found for assigning task: ", children_task)
    else:
        logging.debug("Trying to assign", children_task, "to", assign_to_node)
        status = assign_task_to_remote(assign_to_node, children_task)
        if status == "ok":
            local_children[children_task] = assign_to_node
            call_send_mapping(children_task,assign_to_node)


def get_most_suitable_node(file_size):
    """Calculate network delay + resource delay

    Args:
        file_size (int): file_size

    Returns:
        str: result_node_name - assigned node for the current task
    """
    logging.debug('Trying to get the most suitable node')
    weight_network = 1
    weight_cpu = 1
    weight_memory = 1

    valid_nodes = []
    min_value = sys.maxsize

    valid_net_data = dict()
    for tmp_node_name in network_profile_data:
        data = network_profile_data[tmp_node_name]
        delay = data['a'] * file_size * file_size + data['b'] * file_size + data['c']
        valid_net_data[tmp_node_name] = delay
        if delay < min_value:
            min_value = delay

    for item in valid_net_data:
        if valid_net_data[item] < min_value * threshold:
            valid_nodes.append(item)

    min_value = sys.maxsize
    result_node_name = ''

    task_price_summary = dict()

    for item in valid_nodes:
        tmp_value = valid_net_data[item]
        tmp_cpu = sys.maxsize
        tmp_memory = sys.maxsize
        if item in resource_data.keys():
            tmp_cpu = resource_data[item]['cpu']
            tmp_memory = resource_data[item]['memory']

        tmp_cost = weight_network*tmp_value + weight_cpu*tmp_cpu + weight_memory*tmp_memory

        task_price_summary[item] = weight_network*tmp_value + weight_cpu*tmp_cpu + weight_memory*tmp_memory
        if  tmp_cost < min_value:
            min_value = tmp_cost
            result_node_name = item

    try:
        best_node = min(task_price_summary,key=task_price_summary.get)
        logging.debug('Best node for is ' +best_node)
        return best_node
    except Exception as e:
        logging.debug('Task price summary is not ready yet.....')
        logging.debug(e)
        return -1

def get_resource_data_drupe(MONGO_SVC_PORT):
    """Collect the resource profile from local MongoDB peer
    """

    for profiler_ip in profiler_ips:
        logging.debug('Check Resource Profiler IP: %s',profiler_ip)
        client_mongo = MongoClient('mongodb://'+profiler_ip+':'+str(MONGO_SVC_PORT)+'/')
        db = client_mongo.central_resource_profiler
        collection = db.collection_names(include_system_collections=False)
        logdb =db[profiler_ip].find().skip(db[profiler_ip].count()-1)
        for record in logdb:
            resource_data[network_map[profiler_ip]]={'memory':record['memory'],'cpu':record['cpu'],'last_update':record['last_update']}

    logging.debug('Resource information has already been provided')
    global is_resource_data_ready
    is_resource_data_ready = True

def get_network_data_drupe(my_profiler_ip, MONGO_SVC_PORT, network_map):
    """Collect the network profile from local MongoDB peer
    """
    logging.debug('Check My Network Profiler IP: %s',my_profiler_ip)
    client_mongo = MongoClient('mongodb://'+my_profiler_ip+':'+MONGO_SVC_PORT+'/')
    db = client_mongo.droplet_network_profiler
    collection = db.collection_names(include_system_collections=False)
    num_nb = len(collection)-1
    while num_nb==-1:
        logging.debug('--- Network profiler mongoDB not yet prepared')
        time.sleep(60)
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
    num_rows = db[my_profiler_ip].count()
    while num_rows < num_nb:
        logging.debug('--- Network profiler regression info not yet loaded into MongoDB!')
        time.sleep(60)
        num_rows = db[my_profiler_ip].count()
    logdb =db[my_profiler_ip].find().skip(db[my_profiler_ip].count()-num_nb)
    for record in logdb:
        # Destination ID -> Parameters(a,b,c) , Destination IP
        if record['Destination[IP]'] in home_profiler_ip: continue
        params = re.split(r'\s+', record['Parameters'])
        network_profile_data[network_map[record['Destination[IP]']]] = {'a': float(params[0]), 'b': float(params[1]),
                                                            'c': float(params[2]), 'ip': record['Destination[IP]']}
    logging.debug('Network information has already been provided')

    global is_network_profile_data_ready
    is_network_profile_data_ready = True


def cal_file_size(file_path):
    """Return the file size in bytes

    Args:
        file_path (str): The file path

    Returns:
        float: file size in bytes
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return file_info.st_size * 0.008


if __name__ == '__main__':
    """
        - Prepare global information
        - Initialize folders ``local`` and ``local_responsibility``, prepare ``local_children`` and ``local_mapping`` file.
        - Start thread to get resource profiling data
        - Start thread to get network profiling data
        - Start thread to watch directory: ``local/task_responsibility``
        - Start thread to thread to assign todo task to nodes
    """
    logging.debug(JUPITER_CONFIG_INI_PATH)
    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)

    global FLASK_SVC
    FLASK_SVC    = int(config['PORT']['FLASK_SVC'])

    global control_relation, children, parents, init_tasks, local_children, local_mapping, local_responsibility
    control_relation = {}# control relations between tasks
    children = {}# task's children tasks
    parents = {} # task's parent tasks
    init_tasks = {}# running tasks in node in at the beginning
    local_children = "local/local_children.txt"
    local_mapping = "local/local_mapping.txt"
    local_responsibility = "local/task_responsibility"

    global lock, assigned_tasks, application, MAX_TASK_NUMBER,assignments, manager,network_map,nodes
    manager = Manager()
    assignments = manager.dict()
    assigned_tasks = manager.dict()
    assignments = {}
    network_map = {}
    tmp_nodes_for_convert={}
    nodes = {}
    MAX_TASK_NUMBER = get_num_dag_tasks()

    print(os.environ['WORKER_NODE_NAMES'])
    print(os.environ['WORKER_NODE_IPS'])
    print(os.environ['DRUPE_WORKER_IPS'])
    #Get nodes to self_ip mapping
    for name, node_ip in zip(os.environ['WORKER_NODE_NAMES'].split(":"), os.environ['WORKER_NODE_IPS'].split(":")):
        nodes[name] = node_ip + ":" + str(FLASK_SVC)
    print(nodes)

    #Get nodes to profiler_ip mapping
    for name, node_ip in zip(os.environ['WORKER_NODE_NAMES'].split(":"), os.environ['DRUPE_WORKER_IPS'].split(":")):
        tmp_nodes_for_convert[name] = node_ip
    print(tmp_nodes_for_convert)

    # network_map is a dict that contains node names and profiler ips mapping
    network_map = {v: k for k, v in tmp_nodes_for_convert.items()}

    global threshold, resource_data, is_resource_data_ready, network_profile_data, is_network_profile_data_ready
    threshold = 15
    resource_data = {}
    is_resource_data_ready = False
    network_profile_data = {}
    is_network_profile_data_ready = False
    global first_task
    first_task = os.environ['HOME_CHILD']

    global home_profiler_ip,my_profiler_ip
    my_profiler_ip =os.environ['DRUPE_HOME_IP']
    home_profiler_ip =os.environ['DRUPE_HOME_IP']
    print(home_profiler_ip)

    global profiler_ips
    profiler_ips = os.environ['WORKER_NODE_IPS'].split(':')
    print(profiler_ips)

    # to contact mongoDB on exec prof and drupe
    mongo_svc_port, _ = config['PORT_MAPPINGS']['MONGO'].split(':')

    # Get all information of profilers (drupe network prof, exec prof)
    drupe_worker_ips = os.environ['DRUPE_WORKER_IPS'].split(' ')
    drupe_worker_ips = [info.split(":") for info in drupe_worker_ips]
    drupe_worker_names = [info[0] for info in drupe_worker_ips]
    drupe_pod_ips = [info[1] for info in drupe_worker_ips]
    worker_map = dict(zip(drupe_pod_ips, drupe_worker_names))
    num_workers = len(drupe_worker_ips)
    drupe_home_ip = os.environ['DRUPE_HOME_IP']
    exec_home_ip = os.environ['EXEC_PROF_HOME_IP']

    global node_name, node_id, FLASK_PORT, home_profiler_ip, home_profiler_nodes

    node_name = os.environ['SELF_NAME']
    node_id = int(node_name.split("e")[-1])

    home_profiler = os.environ['DRUPE_HOME_IP'].split(' ')
    home_profiler_nodes = [x.split(':')[0] for x in home_profiler]
    home_profiler_ip = [x.split(':')[1] for x in home_profiler]


    logging.debug("Node name: %s and id %s", node_name, node_id)
    logging.debug("Starting the main thread on port %s", FLASK_PORT)


    global local_mapping, local_children,local_responsibility, manager
    manager = Manager()
    local_mapping = manager.dict()
    local_children = manager.dict()

    local_responsibility = "task_responsibility"
    os.mkdir(local_responsibility)

    init_task_topology()
    # Get resource data
    _thread.start_new_thread(get_resource_data_drupe, (mongo_svc_port,))

    _thread.start_new_thread(et_network_data_drupe, (drupe_home_ip, mongo_svc_port,network_map))

    #monitor Task responsibility folder for the incoming tasks
    w = Watcher()
    w.run()

    while True:
        time.sleep(120)


