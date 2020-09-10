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
from apscheduler.schedulers.background import BackgroundScheduler
import pyinotify


app = Flask(__name__)

def demo_help(server,port,topic,msg):
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()


def prepare_global():
    """Prepare global information (Node info, relations between tasks)
    """

    INI_PATH = '/jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global network_map, FLASK_SVC, MONGO_SVC_PORT, nodes, node_count, master_host, debug, FLASK_PORT

    FLASK_PORT = int(config['PORT']['FLASK_DOCKER'])
    FLASK_SVC  = int(config['PORT']['FLASK_SVC'])
    MONGO_SVC_PORT  = config['PORT']['MONGO_SVC']

    global my_profiler_ip, PROFILER
    PROFILER = int(config['CONFIG']['PROFILER'])
    my_profiler_ip = os.environ['PROFILER']


    # Get ALL node info
    node_count = 0
    nodes = {}
    tmp_nodes_for_convert={}
    network_map = {}

    #Get nodes to self_ip mapping
    for name, node_ip in zip(os.environ['ALL_NODES'].split(":"), os.environ['ALL_NODES_IPS'].split(":")):
        if name == "":
            continue
        nodes[name] = node_ip + ":" + str(FLASK_SVC)
        node_count += 1

    #Get nodes to profiler_ip mapping
    for name, node_ip in zip(os.environ['ALL_NODES'].split(":"), os.environ['ALL_PROFILERS'].split(":")):
        if name == "":
            continue
        #First get mapping like {node: profiler_ip}, and later convert it to {profiler_ip: node}
        tmp_nodes_for_convert[name] = node_ip

    # network_map is a dict that contains node names and profiler ips mapping
    network_map = {v: k for k, v in tmp_nodes_for_convert.items()}

    master_host = os.environ['HOME_IP'] + ":" + str(FLASK_SVC)

    global threshold, resource_data, is_resource_data_ready, network_profile_data, is_network_profile_data_ready, application

    
    threshold = 15
    resource_data = {}
    is_resource_data_ready = False
    network_profile_data = {}
    is_network_profile_data_ready = False
    debug = True

    global control_relation, children, parents

    # control relations between tasks
    control_relation = {}
    children = {}
    parents = {}

    global application
    application = read_file("DAG/DAG_application.txt")
    del application[0]

    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

    print('Bokeh information')
    print(BOKEH_SERVER)
    print(BOKEH_PORT)
    print(BOKEH)

    # global first_task
    global first_task
    first_task = os.environ['CHILD_NODES']

    global profiler_ips 
    profiler_ips = os.environ['ALL_PROFILERS'].split(':')
    profiler_ips = profiler_ips[1:]


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
    print('----------- Control relation')
    print("control_relation" ,control_relation)

def assign_task():
    """Request assigned node for a specific task, write task assignment in local file at ``local_responsibility/task_name``.
    
    Raises:
        Exception: ``ok`` if successful, ``not ok`` if either the request or the writing is failed
    """
    try:

        task_name = request.args.get('task_name')
        parent_name = request.args.get('parent_name')

        local_mapping[task_name] = False
        res = call_send_mapping(task_name, node_name)
        if len(control_relation[task_name])>0:
            print('I am responsible for the next children tasks')
            for task in control_relation[task_name]:
                if task not in local_children.keys():
                    local_children[task] = False
                    t = time.time()
                    content = 'TODO '+ str(t)+'\n'
                    write_file(local_responsibility + "/" + task, content, "w+")
        else:
            print('No children tasks for this task')
        
        return "ok"
    except Exception as e:
        print(e)
        return "not ok"
app.add_url_rule('/assign_task', 'assign_task', assign_task)

def trigger_restart():
    try:
        print('Trigger retart')
        time_info = request.args.get('trigger_restart')
        print('Delete all local information')
        local_mapping.clear()
        local_children.clear()
        return "ok"
    except Exception as e:
        print(e)
        return "not ok"
app.add_url_rule('/trigger_restart', 'trigger_restart', trigger_restart)


def assign_task_to_remote(assigned_node, task_name):
    """Assign task to remote node
    
    Args:
        - assigned_node (str): Node to be assigned
        - task_name (str): task name 
    
    Raises:
        Exception: request if successful, ``not ok`` if failed
    """
    try:
        print('Assign children task to the remote node')
        url = "http://" + nodes[assigned_node] + "/assign_task"
        params = {'parent_name':node_name,'task_name': task_name}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        if BOKEH==3:
            topic = 'msgoverhead_%s'%(node_name)
            msg = 'msgoverhead pricedecoupled controller%s assignremote 1 %s %s \n' %(node_name,task_name,assigned_node)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
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
        print('Announce the mapping to the master host')
        url = "http://" + master_host + "/recv_mapping"
        params = {'mapping': mapping, "node": node}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        local_mapping[mapping] = True
        if BOKEH ==5: 
            topic = 'msgoverhead_%s'%(node_name)
            msg = 'msgoverhead pricedecoupled controller%s announcehome 1 %s %s \n' %(node_name,node,mapping)
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    except Exception as e:
        print(e)
        print("Announce the mapping to the master host failed")
        return 'not ok'
    return 'ok'

def assign_children_task(children_task):
    print('Starting assigning process for the children task')

    while True:
        if is_network_profile_data_ready and is_resource_data_ready:
            break
        else:
            print("Waiting for the profiler data")
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
        print("No suitable node found for assigning task: ", children_task)
    else:
        print("Trying to assign", children_task, "to", assign_to_node)
        status = assign_task_to_remote(assign_to_node, children_task)
        if status == "ok":
            local_children[children_task] = assign_to_node
    return
            

def get_most_suitable_node(file_size):
    """Calculate network delay + resource delay
    
    Args:
        file_size (int): file_size
    
    Returns:
        str: result_node_name - assigned node for the current task
    """
    print('Trying to get the most suitable node')
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

    print('Task price summary')
    print(task_price_summary)

    try:
        best_node = min(task_price_summary,key=task_price_summary.get)
        print('Best node for is ' +best_node)
        return best_node
    except Exception as e:
        print('Task price summary is not ready yet.....') 
        print(e)
        return -1


def read_file(file_name):
    """get all lines in a file
    
    Args:
        file_name (str): file path
    
    Returns:
        str: file_contents - all lines in a file
    """
    file_contents = []
    file = open(file_name)
    line = file.readline()
    while line:
        file_contents.append(line)
        line = file.readline()
    file.close()
    return file_contents


def output(msg):
    """if debug is True, print the msg
    
    Args:
        msg (str): message to be printed
    """
    if debug:
        print(msg)

def get_resource_data_drupe(MONGO_SVC_PORT):
    """Collect the resource profile from local MongoDB peer
    """

    for profiler_ip in profiler_ips:
        print('Check Resource Profiler IP: '+profiler_ip)
        client_mongo = MongoClient('mongodb://'+profiler_ip+':'+str(MONGO_SVC_PORT)+'/')
        db = client_mongo.central_resource_profiler
        collection = db.collection_names(include_system_collections=False)
        logging =db[profiler_ip].find().skip(db[profiler_ip].count()-1)
        for record in logging:
            resource_data[network_map[profiler_ip]]={'memory':record['memory'],'cpu':record['cpu'],'last_update':record['last_update']}

    global is_resource_data_ready
    is_resource_data_ready = True

    if BOKEH==3:
        topic = 'msgoverhead_%s'%(node_name)
        msg = 'msgoverhead pricedecoupled%s resourcedata %d \n' %(node_name,len(profiler_ips))
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)


def get_network_data_drupe(my_profiler_ip, MONGO_SVC_PORT, network_map):
    """Collect the network profile from local MongoDB peer
    """
    print('Check My Network Profiler IP: '+my_profiler_ip)
    client_mongo = MongoClient('mongodb://'+my_profiler_ip+':'+MONGO_SVC_PORT+'/')
    db = client_mongo.droplet_network_profiler
    collection = db.collection_names(include_system_collections=False)
    num_nb = len(collection)-1
    while num_nb==-1:
        print('--- Network profiler mongoDB not yet prepared')
        time.sleep(60)
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
    print('--- Number of neighbors: '+str(num_nb))
    num_rows = db[my_profiler_ip].count()
    while num_rows < num_nb:
        print('--- Network profiler regression info not yet loaded into MongoDB!')
        time.sleep(60)
        num_rows = db[my_profiler_ip].count()
    logging =db[my_profiler_ip].find().skip(db[my_profiler_ip].count()-num_nb)


    c = 0
    for record in logging:
        # Destination ID -> Parameters(a,b,c) , Destination IP

        if record['Destination[IP]'] in home_profiler_ip: continue
        params = re.split(r'\s+', record['Parameters'])
        network_profile_data[network_map[record['Destination[IP]']]] = {'a': float(params[0]), 'b': float(params[1]),
                                                            'c': float(params[2]), 'ip': record['Destination[IP]']}
        c = c+1
    print('Network information has already been provided')

    global is_network_profile_data_ready
    is_network_profile_data_ready = True

    if BOKEH==3:
        topic = 'msgoverhead_%s'%(node_name)
        msg = 'msgoverhead pricedecoupled controller%s networkdata %d \n' %(node_name,c)
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)



def profilers_mapping_decorator(f):
    """General Mapping decorator function
    """
    @wraps(f)
    def profiler_mapping(*args, **kwargs):
      return f(*args, **kwargs)
    return profiler_mapping

def get_network_data_mapping():
    """Mapping the chosen TA2 module (network monitor) based on ``jupiter_config.PROFILER`` in ``jupiter_config.ini``
    
    Args:
        PROFILER (str): specified from ``jupiter_config.ini``
    
    Returns:
        TYPE: corresponding network function
    """
    if PROFILER==0: 
        return profilers_mapping_decorator(get_network_data_drupe)
    return profilers_mapping_decorator(get_network_data_drupe)

def get_resource_data_mapping():
    """Mapping the chosen TA2 module (resource monitor) based on ``jupiter_config.PROFILER`` in ``jupiter_config.ini``
    
    Args:
        PROFILER (str): specified from ``jupiter_config.ini``
    
    Returns:
        TYPE: corresponding resource function
    """
    if PROFILER==0: 
        return profilers_mapping_decorator(get_resource_data_drupe)
    return profilers_mapping_decorator(get_resource_data_drupe)

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

def schedule_update_profiling(interval):
    """
    Schedulete the assignment update every interval
    
    Args:
        interval (int): chosen interval (minutes)
    
    """
    sched = BackgroundScheduler()
    get_network_data = get_network_data_mapping()
    get_resource_data = get_resource_data_mapping()
    sched.add_job(get_network_data,'interval',[my_profiler_ip, MONGO_SVC_PORT,network_map],id='network_profiling', minutes=interval, replace_existing=True)
    sched.add_job(get_resource_data,'interval',[MONGO_SVC_PORT],id='resource_profiling', minutes=interval, replace_existing=True)
    sched.start()

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_PORT)

class MyEventHandler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """

    def process_IN_CLOSE_WRITE(self, event):
        print("CREATE CLOSE event:", event.pathname)
        t = time.time()
        # print(t)
        new_task = os.path.split(event.pathname)[-1]
        _thread.start_new_thread(assign_children_task,(new_task,))

def main():
    """
        - Prepare global information
        - Initialize folders ``local`` and ``local_responsibility``, prepare ``local_children`` and ``local_mapping`` file.
        - Start thread to get resource profiling data
        - Start thread to get network profiling data
        - Start thread to watch directory: ``local/task_responsibility``
        - Start thread to thread to assign todo task to nodes
    """
    
    prepare_global()

    global node_name, node_id, FLASK_PORT, home_profiler_ip, home_profiler_nodes

    node_name = os.environ['SELF_NAME']
    node_id = int(node_name.split("e")[-1])

    home_profiler = os.environ['HOME_PROFILER_IP'].split(' ')
    home_profiler_nodes = [x.split(':')[0] for x in home_profiler]
    home_profiler_ip = [x.split(':')[1] for x in home_profiler]


    print("Node name:", node_name, "and id", node_id)
    print("Starting the main thread on port", FLASK_PORT)


    global local_mapping, local_children,local_responsibility, manager
    manager = Manager()
    local_mapping = manager.dict()
    local_children = manager.dict()

    local_responsibility = "task_responsibility"
    os.mkdir(local_responsibility)

    init_task_topology()

    web_server = MonitorRecv()
    web_server.start()

    global get_network_data, get_resource_data

    update_interval = 1
    _thread.start_new_thread(schedule_update_profiling,(update_interval,))
    # watch manager
    wm = pyinotify.WatchManager()
    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'task_responsibility')

    wm.add_watch(DIRECTORY_TO_WATCH, pyinotify.ALL_EVENTS, rec=True)
    print('starting the process\n')
    # event handler
    eh = MyEventHandler()
    # notifier
    notifier = pyinotify.Notifier(wm, eh)

    notifier.loop()


if __name__ == '__main__':
    main()
    
