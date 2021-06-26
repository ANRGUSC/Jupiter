"""
.. note:: This is the main script to run in home node for greedy WAVE.
"""
__author__ = "Quynh Nguyen, Pranav Sakulkar, Jiatong Wang, Pradipta Ghosh, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

import re
import threading
import os
import urllib
import json
import sys
import _thread
import time
from flask import Flask, request
import configparser
from os import path
import multiprocessing
from multiprocessing import Process, Manager
import paho.mqtt.client as mqtt
from functools import wraps
from pymongo import MongoClient
from flask import Flask, request
import requests
import logging
from build.jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
"""Paths specific to container (see Dockerfile)"""
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
APP_DIR = "/jupiter/build/app_specific_files/"
app = Flask(__name__)

def recv_task_assign_info():
    """
        Receive task assignment information from the workers
    """
    assign = request.args.get('assign')
    task_assign_summary.append(assign)
    log.debug("Task assign summary: " + json.dumps(task_assign_summary))
    return 'ok'
app.add_url_rule('/recv_task_assign_info', 'recv_task_assign_info', recv_task_assign_info)


def recv_mapping():
    """
    From each droplet, the master receive the local mapping of the assigned task for that droplet, combine all of the information
    Write the global mapping to ``assignments`` variable and ``local/input_to_CIRCE.txt``

    Returns:
        str: ``ok`` if mapping is ready, ``not ok`` otherwise

    Raises:
        Exception:   when mapping is not ready
    """

    try:
        log.debug('Receive mapping from the workers')
        node = request.args.get('node')
        mapping = request.args.get("mapping")
        to_be_write = []
        items = re.split(r'#', mapping)
        for _, p in enumerate(items):
            p = p.strip()
            assigned_tasks[p] = 1
            assignments[p] = node
            to_be_write.append(p + '\t' + node)
            log.debug('Receive mapping of %s to node %s'%(p,node))
        write_file("input_to_CIRCE.txt", to_be_write, "a+")
    except Exception as e:
        log.debug(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_mapping', 'recv_mapping', recv_mapping)

def assign_task_to_remote(assigned_node, task_name):
    """
    A function that used for intermediate data transfer. Assign initial task mapping to corresponding node, used in `init_thread()`

    Args:
        - assigned_node (str): node which is assigned to the task
        - task_name (str): name of the task

    Returns:
        str: request if sucessful, ``not ok`` otherwise
    """
    try:
        log.debug('Assign the first task')
        url = "http://" + nodes[assigned_node] + "/assign_task"
        log.debug(url)
        params = {'task_name': task_name}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        log.debug(e)
        return "not ok"
    return res

def init_thread():
    """
    Assign the first task
    """
    time.sleep(60)
    log.debug('--------------- Assign task to remote node')
    for key in init_tasks:
        tasks = init_tasks[key]
        for _, task in enumerate(tasks):
            res = assign_task_to_remote(key, task)
            if res == "ok":
                log.debug("Assign task %s to node %s" % (task, key))
            else:
                log.debug("Assign task %s to node %s failed" % (task, key))

def write_file(file_name, content, mode):
    """
    Write the content to file

    Args:
        - file_name (str): file path
        - content (str): content to be written
        - mode (str): write mode
    """
    file = open(file_name, mode)
    for line in content:
        file.write(line + "\n")
    file.close()


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


def get_most_suitable_node():
    """Calculate esource delay
    Returns:
        str: result_node_name - assigned node for the current task
    """
    # No network information for home node in version 5
    log.debug('Trying to get the most suitable node')
    weight_cpu = 1
    weight_memory = 1
    task_price_summary = dict()
    for item in resource_data:
        task_price_summary[item] = weight_cpu* resource_data[item]['cpu'] + weight_memory*resource_data[item]['memory']

    try:
        log.debug(task_price_summary)
        best_node = min(task_price_summary,key=task_price_summary.get)
        log.debug('Best node is ' +best_node)
        return best_node
    except Exception as e:
        log.debug('Task price summary is not ready yet.....')
        return -1

def init_task_topology():
    """
        - Read ``DAG/input_node.txt``, get inital task information for each node
        - Read ``DAG/DAG_application.txt``, get parent list of child tasks
        - Create the DAG
        - Write control relations to ``DAG/parent_controller.txt``
    """
    assign_to_node = -1
    while assign_to_node==-1:
        assign_to_node = get_most_suitable_node()
        time.sleep(1)
    init_tasks[assign_to_node] = [first_task]
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

def return_task_mapping():
    """Respond with the task mapping only when it's finished. Otherwise,
    respond with an empty dict.

    Returns:
        json: task mapping of tasks and corresponding nodes
    """
    if num_tasks < 0:
        log.error("invalid number of tasks")

    log.info("Received request for task mapping. Current mappings done: %d" %len(assignments))
    log.info("task mapping: " + json.dumps(assignments.copy(), indent=4))
    if len(assignments) == num_tasks:
        return json.dumps(assignments.copy())
    else:
        log.info('task_mapping not yet finished, responding with empty dict()')
        return json.dumps(dict())
app.add_url_rule('/', 'return_task_mapping', return_task_mapping)
  
if __name__ == '__main__':
    app_config = app_config_parser.AppConfig(APP_DIR)
    log.debug(JUPITER_CONFIG_INI_PATH)
    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)

    global num_tasks
    task_names = app_config.get_dag_task_names()
    num_tasks = len(task_names)

    flask_svc, flask_port = config['PORT_MAPPINGS']['FLASK'].split(':')

    global control_relation, children, parents, init_tasks
    control_relation = {}# control relations between tasks
    children = {}# task's children tasks
    parents = {} # task's parent tasks
    init_tasks = {}# running tasks in node in at the beginning

    global lock, assigned_tasks, assignments, manager
    manager = Manager()
    assignments = manager.dict()
    assigned_tasks = manager.dict()

    global resource_data, is_resource_data_ready, dag_task_map
    resource_data = {}
    is_resource_data_ready = False
    dag_task_map = app_config.dag_task_map()

    global drupe_worker_ips, drupe_worker_names, profiler_ips, drupe_ip2name, drupe_name2ip, num_workers
    global home_profiler_ip,my_profiler_ip, first_task, mongo_svc_port
    global worker_ips, worker_names, nodes
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
    my_profiler_ip =os.environ['DRUPE_HOME_IP']
    home_profiler_ip =os.environ['DRUPE_HOME_IP']
    first_task = os.environ['FIRST_TASK']
    worker_ips = os.environ['WORKER_NODE_IPS'].split(':')
    worker_names = os.environ['WORKER_NODE_NAMES'].split(':')
    workers = [ip+ ":" + str(flask_svc) for ip in worker_ips]
    nodes = dict(zip(worker_names,workers))

    # to contact mongoDB on exec prof and drupe
    mongo_svc_port, _ = config['PORT_MAPPINGS']['MONGO'].split(':')


    _thread.start_new_thread(get_resource_data_drupe, (mongo_svc_port,))
    starting_time = time.time()
    init_task_topology()
    _thread.start_new_thread(init_thread, ())
    app.run(host='0.0.0.0', port=int(flask_port))
    while True:
        if len(assigned_tasks) == num_tasks:
            log.debug('Successfully finished WAVE greedy task_mapping')
            end_time = time.time()
            deploy_time = end_time - starting_time
            log.debug('Time to finish WAVE task mapping %f'%(deploy_time))
            break
        else:
            log.debug('Waiting for all the assignments...')
            time.sleep(5)    
    


