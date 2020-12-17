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
from build.jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

"""Paths specific to container (see Dockerfile)"""
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
APP_DIR = "/jupiter/build/app_specific_files/"
app = Flask(__name__)

def init_task_topology():
    """
        - Create the DAG
        - Write control relations to ``DAG/parent_controller.txt``
    """

    for task in dag_task_map:
        for child in dag_task_map[task]:
            if child not in parents:
                parents[child] = [task]
            else:
                parents[child].append(task)
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
    log.debug('----------- Control relation')
    log.debug(control_relation)

def assign_task():
    """Request assigned node for a specific task, write task assignment in local file at ``local_responsibility/task_name``.

    Raises:
        Exception: ``ok`` if successful, ``not ok`` if either the request or the writing is failed
    """
    try:
        log.debug('Receive task assignment')
        task_name = request.args.get('task_name')
        local_mapping[task_name] = False
        res = call_send_mapping(task_name, node_name)
        if len(control_relation[task_name])>0:
            for task in control_relation[task_name]:
                if task not in local_children.keys():
                    local_children[task] = False
                    write_file(local_responsibility + "/" + task, 'TODO', "w+")
        else:
            log.debug('No children tasks for this task')
        return "ok"
    except Exception as e:
        log.debug(e)
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
        log.debug('Assign children task to the remote node')
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
    file.write(content + "\n")
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
        log.debug('Announce the mapping to the master host')
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
            log.debug("Received file as input - %s." % event.src_path)
            new_task = os.path.split(event.src_path)[-1]
            _thread.start_new_thread(assign_children_task,(new_task,))


def assign_children_task(children_task):
    log.debug('Starting assigning process for the children task')
    while True:
        if is_network_profile_data_ready and is_resource_data_ready:
            break
        else:
            log.debug("Waiting for the profiler data")
            time.sleep(100)
    res = False
    sample_file = SAMPLE_FILE_PATH
    sample_size = cal_file_size(sample_file)
    assign_to_node = get_most_suitable_node(sample_size)
    if not assign_to_node:
        log.debug("No suitable node found for assigning task: %s" %(children_task))
    else:
        log.debug("Trying to assign %s to %s" %(children_task, assign_to_node))
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
    log.debug('Trying to get the most suitable node')
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
        log.debug('Best node is %s'%(best_node))
        return best_node
    except Exception as e:
        log.debug('Task price summary is not ready yet.....')
        return -1

def get_resource_data_drupe(mongo_svc_port):
    """Collect the resource profile from local MongoDB peer
    """
    for profiler_ip in profiler_ips:
        log.debug('Check Resource Profiler IP: %s',profiler_ip)
        client_mongo = MongoClient('mongodb://'+profiler_ip+':'+str(mongo_svc_port)+'/')
        db = client_mongo.central_resource_profiler
        collection = db.collection_names(include_system_collections=False)
        logdb =db[profiler_ip].find().skip(db[profiler_ip].count()-1)
        for record in logdb:
            resource_data[drupe_ip2name[profiler_ip]]={'memory':record['memory'],'cpu':record['cpu'],'last_update':record['last_update']}
    log.debug('Resource information has already been provided')
    global is_resource_data_ready
    is_resource_data_ready = True

def get_network_data_drupe(my_profiler_ip, mongo_svc_port, drupe_ip2name):
    """Collect the network profile from local MongoDB peer
    """
    log.debug('Check My Network Profiler IP: %s'%(my_profiler_ip))
    client_mongo = MongoClient('mongodb://'+my_profiler_ip+':'+mongo_svc_port+'/')
    db = client_mongo.droplet_network_profiler
    collection = db.collection_names(include_system_collections=False)
    num_nb = len(collection)-1
    while num_nb==-1:
        log.debug('--- Network profiler mongoDB not yet prepared')
        time.sleep(60)
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
    num_rows = db[my_profiler_ip].count()
    while num_rows < num_nb:
        log.debug('--- Network profiler regression info not yet loaded into MongoDB!')
        time.sleep(60)
        num_rows = db[my_profiler_ip].count()
    logdb =db[my_profiler_ip].find().skip(db[my_profiler_ip].count()-num_nb)
    for record in logdb:
        # Destination ID -> Parameters(a,b,c) , Destination IP
        if record['Destination[IP]'] in home_profiler_ip: continue
        params = re.split(r'\s+', record['Parameters'])
        network_profile_data[drupe_ip2name[record['Destination[IP]']]] = {'a': float(params[0]), 'b': float(params[1]),
                                                            'c': float(params[2]), 'ip': record['Destination[IP]']}
    log.debug('Network information has already been provided')
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
    app_config = app_config_parser.AppConfig(APP_DIR)
    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)
    flask_svc, flask_port = config['PORT_MAPPINGS']['FLASK'].split(':')
    global num_tasks
    task_names = app_config.get_dag_task_names()
    num_tasks = len(task_names)
    global dag_task_map,control_relation, children, parents, init_tasks, SAMPLE_FILE_PATH
    SAMPLE_FILE_PATH = os.path.join(APP_DIR,app_config.get_wave_sample())
    dag_task_map = app_config.dag_task_map()
    control_relation = {}# control relations between tasks
    children = {}# task's children tasks
    parents = {} # task's parent tasks
    init_tasks = {}# running tasks in node in at the beginning
    global assigned_tasks, assignments, manager,local_mapping, local_children,local_responsibility
    manager = Manager()
    assignments = manager.dict()
    assigned_tasks = manager.dict()
    assignments = {}
    local_mapping = manager.dict()
    local_children = manager.dict()
    local_responsibility = "task_responsibility"
    os.mkdir(local_responsibility)
    global threshold, resource_data, is_resource_data_ready, network_profile_data, is_network_profile_data_ready
    threshold = 15
    resource_data = {}
    is_resource_data_ready = False
    network_profile_data = {}
    is_network_profile_data_ready = False
    global drupe_worker_ips, drupe_worker_names, profiler_ips, drupe_ip2name, drupe_name2ip, num_workers,master_host
    global home_profiler_ip,my_profiler_ip, mongo_svc_port,node_name,nodes
    # Get all information of profilers (drupe network prof, exec prof)
    drupe_worker_ips = os.environ['DRUPE_WORKER_IPS'].split(' ')
    drupe_worker_ips = [info.split(":") for info in drupe_worker_ips]
    drupe_worker_names = [info[0] for info in drupe_worker_ips]
    profiler_ips = [info[1] for info in drupe_worker_ips]
    drupe_ip2name = dict(zip(profiler_ips, drupe_worker_names))
    drupe_name2ip = dict(zip(drupe_worker_names,profiler_ips))
    num_workers = len(drupe_worker_ips)
    drupe_home_ip = os.environ['DRUPE_HOME_IP']
    exec_home_ip = os.environ['EXEC_PROF_HOME_IP']
    home_profiler_ip =os.environ['DRUPE_HOME_IP']
    # to contact mongoDB on exec prof and drupe
    mongo_svc_port, _ = config['PORT_MAPPINGS']['MONGO'].split(':')
    node_name = os.environ['NODE_NAME']
    my_profiler_ip = drupe_name2ip[node_name]
    worker_ips = os.environ['WORKER_NODE_IPS'].split(':')
    worker_names = os.environ['WORKER_NODE_NAMES'].split(':')
    workers = [ip+ ":" + str(flask_svc) for ip in worker_ips]
    nodes = dict(zip(worker_names,workers))
    master_host = os.environ['HOME_NODE_IP'] + ":" + str(flask_svc)

    init_task_topology()
    # Get resource data
    _thread.start_new_thread(get_resource_data_drupe, (mongo_svc_port,))
    _thread.start_new_thread(get_network_data_drupe, (my_profiler_ip, mongo_svc_port,drupe_ip2name))
    #monitor Task responsibility folder for the incoming tasks
    w = Watcher()
    w.run()
    app.run(host='0.0.0.0', port=int(flask_port))



