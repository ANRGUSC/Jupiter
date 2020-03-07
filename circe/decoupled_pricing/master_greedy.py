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
import requests
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

def read_file(file_name):
    """
    Get all lines in a file
    
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

def prepare_global():
    """
    Prepare global information (Node info, relations between tasks, initial task)
    """

    INI_PATH = '/jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global FLASK_PORT, FLASK_SVC, MONGO_SVC_PORT, nodes, node_count, master_host

    FLASK_PORT = int(config['PORT']['FLASK_DOCKER'])
    FLASK_SVC  = int(config['PORT']['FLASK_SVC'])
    MONGO_SVC_PORT = int(config['PORT']['MONGO_SVC'])

    global BOKEH_SERVER, BOKEH_PORT, BOKEH, app_name, app_option
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])
    app_name = os.environ['APP_NAME']
    app_option = os.environ['APP_OPTION']

    global node_name 
    node_name = os.environ['SELF_NAME']


    print("starting the main thread on port")

    
    global task_assign_summary, docker_ip2node_name
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

    global node_id, debug
    node_id = -1
    
    debug = True

    global control_relation, children, parents, init_tasks, local_children, local_mapping, local_responsibility

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

    global lock, assigned_tasks, application, MAX_TASK_NUMBER,assignments, manager
    manager = Manager()
    assignments = manager.dict()
    assigned_tasks = manager.dict()

    application = read_file("DAG/DAG_application.txt")
    MAX_TASK_NUMBER = int(application[0])  # Total number of tasks in the DAG 
    print("Max task number ", MAX_TASK_NUMBER)
    del application[0]

    # assignments = {}

    global compute_home_host
    compute_home_host = os.environ['COMPUTE_HOME_IP']+':'+ str(FLASK_SVC)

    
    global first_task
    first_task = os.environ['CHILD_NODES']

    global profiler_ips 
    profiler_ips = os.environ['ALL_PROFILERS'].split(':')
    profiler_ips = profiler_ips[1:]

    global threshold, resource_data, is_resource_data_ready, network_profile_data, is_network_profile_data_ready

    
    threshold = 15
    resource_data = {}
    is_resource_data_ready = False
    network_profile_data = {}
    is_network_profile_data_ready = False

    global my_profiler_ip, network_map, PROFILER
    PROFILER = int(config['CONFIG']['PROFILER'])
    my_profiler_ip = os.environ['PROFILER']

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

    global home_profiler_ip
    home_profiler = os.environ['HOME_PROFILER_IP'].split(' ')
    home_profiler_ip = [x.split(':')[1] for x in home_profiler]

def recv_task_assign_info():
    """
        Receive task assignment information from the workers
    """
    assign = request.args.get('assign')
    task_assign_summary.append(assign)
    print("Task assign summary: " + json.dumps(task_assign_summary))
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
        print('Receive mapping from the workers')
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
        print('Receive mapping from the workers failed')
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_mapping', 'recv_mapping', recv_mapping)


def announce_mapping_to_homecompute():
    try:
        print('Announce full mapping to compute home node') 
        tmp_assignments = ",".join(("{}:{}".format(*i) for i in assignments.items()))
        url = "http://" + compute_home_host + "/announce_mapping"
        params = {'assignments': tmp_assignments}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        if BOKEH==3:
            msg = 'msgoverhead pricedecoupled controllerhome announcehomecompute 1 \n'
            demo_help(BOKEH_SERVER,BOKEH_PORT,"msgoverhead_home",msg)
    except Exception as e:
        print('Announce full mapping to compute home node failed')
        print(e)
        return "not ok"
    return res

def trigger_restart(flask_info):
    try:
        print('Trigger retart')
        url = "http://" + flask_info + "/trigger_restart"
        t = time.time()
        params = {'trigger_restart': t}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print('Trigger restart failed')
        print(e)
        return "not ok"
    return res
    
def restart_mapping_process():
    print('Restart the mapping process')
    for node in nodes:
        trigger_restart(nodes[node])
    if BOKEH==3:
        msg = 'msgoverhead pricedecoupled controllerhome triggerrestart %d\n'%(len(nodes))
        demo_help(BOKEH_SERVER,BOKEH_PORT,"msgoverhead_home",msg)
    print('Send the first task to the first node')
    _thread.start_new_thread(init_thread, ())


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
        print('Assign the first task based on the input file')
        url = "http://" + nodes[assigned_node] + "/assign_task"
        params = {'parent_name':node_name,'task_name': task_name}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
        if BOKEH==3:
            msg = 'msgoverhead pricedecoupled controllerhome assignfirst 1 \n'
            demo_help(BOKEH_SERVER,BOKEH_PORT,"msgoverhead_home",msg)
    except Exception as e:
        print(e)
        return "not ok"
    return res



def init_thread():
    """
    Assign the first task
    """
    time.sleep(10)
    print('--------------- Init thread')
    for key in init_tasks:
        tasks = init_tasks[key]
        for _, task in enumerate(tasks):
            res = assign_task_to_remote(key, task)
            if res == "ok":
                output("Assign task %s to node %s" % (task, key))
            else:
                output("Assign task %s to node %s failed" % (task, key))
    return

def monitor_task_status(starting_time):
    """
    Monitor task allocation status and print notification if all task allocations are done
    """

    killed = 0
    while True:
        print('Monitoring task status')
        print(assignments)
        if len(assigned_tasks) == MAX_TASK_NUMBER:
            print("All task allocations are done! Great News!")
            end_time = time.time()
            deploy_time = end_time - starting_time
            print('Time to finish WAVE mapping '+ str(deploy_time))
            if BOKEH==3:
                topic = 'mappinglatency_%s'%(app_option)
                msg = 'mappinglatency pricedecoupled controllerhome %s %f \n' %(app_name,deploy_time)
                demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)

            print("Announce assignment information to the compute home node")
            announce_mapping_to_homecompute()
            print('Delete full mapping information')
            assignments.clear()
            assigned_tasks.clear()
            restart_mapping_process()
            starting_time = time.time()
            
        else:
            print('Waiting for task mapping to be finished!!!!')
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
    print('Check My Network Profiler IP: '+my_profiler_ip)
    client_mongo = MongoClient('mongodb://'+my_profiler_ip+':'+str(MONGO_SVC_PORT)+'/')
    db = client_mongo.droplet_network_profiler
    collection = db.collection_names(include_system_collections=False)
    num_nb = len(collection)-1
    while num_nb==-1:
        print('--- Network profiler mongoDB not yet prepared')
        time.sleep(60)
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
    num_rows = db[my_profiler_ip].count()
    while num_rows < num_nb:
        print('--- Network profiler regression info not yet loaded into MongoDB!')
        time.sleep(60)
        num_rows = db[my_profiler_ip].count()
    logging =db[my_profiler_ip].find().skip(db[my_profiler_ip].count()-num_nb)
    for record in logging:
        # Destination ID -> Parameters(a,b,c) , Destination IP
        if record['Destination[IP]'] in home_profiler_ip: continue
        params = re.split(r'\s+', record['Parameters'])
        network_profile_data[network_map[record['Destination[IP]']]] = {'a': float(params[0]), 'b': float(params[1]),
                                                            'c': float(params[2]), 'ip': record['Destination[IP]']}
    print('Network information has already been provided')

    global is_network_profile_data_ready
    is_network_profile_data_ready = True

    if BOKEH==3:
        topic = 'msgoverhead_%s'%(node_name)
        msg = 'msgoverhead pricedecoupled controllerhome%s networkdata %d \n' %(node_name,num_nb)
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)

def profilers_mapping_decorator(f):
    """General Mapping decorator function
    """
    @wraps(f)
    def profiler_mapping(*args, **kwargs):
      return f(*args, **kwargs)
    return profiler_mapping


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

    print('Resource information has already been provided')
    global is_resource_data_ready
    is_resource_data_ready = True

    if BOKEH==3:
        topic = 'msgoverhead_%s'%(node_name)
        msg = 'msgoverhead pricedecoupled controllerhome%s resourcedata %d \n' %(node_name,len(profiler_ips))
        demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)

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

    print('------- Init tasks')
    print("init_tasks" ,init_tasks)

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

def output(msg):
    """
    if debug is True, print the msg
    
    Args:
        msg (str): message to be printed
    """
    if debug:
        print(msg)

def main():
    """
        - Prepare global information
        - Start the main thread: get inital task information for each node, get parent list of child tasks, Update control relations between tasks in the system
        - Start thread to watch directory: ``local/task_responsibility``
        - Start thread to monitor task mapping status
    """
    global starting_time
    print('Starting to run WAVE mapping')
    starting_time = time.time()
    prepare_global()

    print("starting the main thread on port", FLASK_PORT)

    update_interval = 1
    _thread.start_new_thread(schedule_update_profiling,(update_interval,))

    init_task_topology()
    _thread.start_new_thread(init_thread, ())
    _thread.start_new_thread(monitor_task_status, (starting_time,))
    app.run(host='0.0.0.0', port=int(FLASK_PORT))

if __name__ == '__main__':
    main()

