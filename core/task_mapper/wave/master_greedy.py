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

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

"""Paths specific to container (see Dockerfile)"""
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
WAVE_FILES_DIR = '/jupiter/'




app = Flask(__name__)



def recv_task_assign_info():
    """
        Receive task assignment information from the workers
    """
    assign = request.args.get('assign')
    task_assign_summary.append(assign)
    logging.debug("Task assign summary: " + json.dumps(task_assign_summary))
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
        logging.debug('Receive mapping from the workers')
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
    except Exception as e:
        logging.debug(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_mapping', 'recv_mapping', recv_mapping)

def return_assignment():
    """
    Return mapping assignments which have been finished at the current time of request.

    Returns:
        json: mapping assignments
    """
    logging.debug("Recieved request for current mapping. Current mappings done: %d", len(assignments))
    if len(assignments) == MAX_TASK_NUMBER:
        logging.debug(assignments)
        return json.dumps(assignments)
    else:
        return json.dumps(dict())
app.add_url_rule('/', 'return_assignment', return_assignment)

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
        logging.debug('Assign the first task')
        url = "http://" + nodes[assigned_node] + "/assign_task"
        params = {'task_name': task_name}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        if BOKEH==3:
            msg = 'msgoverhead greedywavehome assignfirst 1 \n'
    except Exception as e:
        logging.debug(e)
        return "not ok"
    return res




def init_thread():
    """
    Assign the first task
    """
    time.sleep(60)
    logging.debug('--------------- Init thread')
    for key in init_tasks:
        # logging.debug(key)
        tasks = init_tasks[key]
        for _, task in enumerate(tasks):
            res = assign_task_to_remote(key, task)
            if res == "ok":
                logging.debug("Assign task %s to node %s" % (task, key))
            else:
                logging.debug("Assign task %s to node %s failed" % (task, key))


def monitor_task_status():
    """
    Monitor task allocation status and logging.debug notification if all task allocations are done
    """

    killed = 0
    while True:
        if len(assigned_tasks) == MAX_TASK_NUMBER:
            logging.debug(assigned_tasks)
            logging.debug("All task allocations are done! Great News!")
            end_time = time.time()
            deploy_time = end_time - starting_time
            logging.debug('Time to finish WAVE mapping '+ str(deploy_time))
            break
        time.sleep(5)



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

def get_network_data_drupe(my_profiler_ip, MONGO_SVC_PORT, network_map):
    """Collect the network profile from local MongoDB peer
    """
    logging.debug('Check My Network Profiler IP: %s',my_profiler_ip)
    client_mongo = MongoClient('mongodb://'+my_profiler_ip+':'+str(MONGO_SVC_PORT)+'/')
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

    logging.debug('Input profiling information')
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

    logging.debug('Task price summary')
    logging.debug(task_price_summary)

    try:
        best_node = min(task_price_summary,key=task_price_summary.get)
        logging.debug('Best node for is ' +best_node)
        return best_node
    except Exception as e:
        logging.debug('Task price summary is not ready yet.....')
        logging.debug(e)
        return -1

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

def init_task_topology():
    """
        - Read ``DAG/input_node.txt``, get inital task information for each node
        - Read ``DAG/DAG_application.txt``, get parent list of child tasks
        - Create the DAG
        - Write control relations to ``DAG/parent_controller.txt``
    """

    sample_file = '/1botnet.ipsum'
    sample_size = cal_file_size(sample_file)

    assign_to_node = -1
    while assign_to_node==-1:
        assign_to_node = get_most_suitable_node(sample_size)
        time.sleep(60)
    init_tasks[assign_to_node] = [first_task]
    logging.debug('------- Init tasks')
    logging.debug("init_tasks" ,init_tasks)

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


    
if __name__ == '__main__':
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

    logging.debug("starting the main thread on port %d", FLASK_PORT)

    _thread.start_new_thread(get_resource_data_drupe, (mongo_svc_port,))

    _thread.start_new_thread(et_network_data_drupe, (drupe_home_ip, mongo_svc_port,network_map))

    init_task_topology()
    _thread.start_new_thread(init_thread, ())
    _thread.start_new_thread(monitor_task_status, ())
    
    while True:
        time.sleep(120)


