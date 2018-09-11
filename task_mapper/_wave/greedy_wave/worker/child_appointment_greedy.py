"""
.. note:: This is the main script to run in every worker node for greedy WAVE.
"""
__author__ = "Pranav Sakulkar, Jiatong Wang, Pradipta Ghosh, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

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

app = Flask(__name__)


def prepare_global():
    """Prepare global information (Node info, relations between tasks)
    """

    INI_PATH = '/jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global network_map, FLASK_PORT, FLASK_SVC, MONGO_SVC_PORT, nodes, node_count, master_host, node_id, node_name, debug

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
    for node_name, node_ip in zip(os.environ['ALL_NODES'].split(":"), os.environ['ALL_NODES_IPS'].split(":")):
        if node_name == "":
            continue
        nodes[node_name] = node_ip + ":" + str(FLASK_SVC)
        node_count += 1

    #Get nodes to profiler_ip mapping
    for node_name, node_ip in zip(os.environ['ALL_NODES'].split(":"), os.environ['ALL_PROFILERS'].split(":")):
        if node_name == "":
            continue
        #First get mapping like {node: profiler_ip}, and later convert it to {profiler_ip: node}
        tmp_nodes_for_convert[node_name] = node_ip

    # network_map is a dict that contains node names and profiler ips mapping
    network_map = {v: k for k, v in tmp_nodes_for_convert.items()}

    master_host = os.environ['HOME_IP'] + ":" + str(FLASK_SVC)
    print("Nodes", nodes)
    print(network_map)



    global threshold, resource_data, is_resource_data_ready, network_profile_data, is_network_profile_data_ready

    
    threshold = 15
    resource_data = {}
    is_resource_data_ready = False
    network_profile_data = {}
    is_network_profile_data_ready = False

    node_id = -1
    node_name = ""
    debug = True

    global control_relation, children, parents, init_tasks, local_children, local_mapping, local_responsibility

    # control relations between tasks
    control_relation = {}

    local_children = "local/local_children.txt"
    local_mapping = "local/local_mapping.txt"
    local_responsibility = "local/task_responsibility"

    global lock, kill_flag

    # lock for sync file operation
    lock = threading.Lock()
    kill_flag = False

def assign_task():
    """Request assigned node for a specific task, write task assignment in local file at ``local_responsibility/task_name``.
    
    Raises:
        Exception: ``ok`` if successful, ``not ok`` if either the request or the writing is failed
    """
    try:

        task_name = request.args.get('task_name')
        print('Assigned task -------------------')
        print(task_name)
        write_file(local_responsibility + "/" + task_name, [], "w+")
        print('Done assign task ----------------------------------')
        return "ok"
    except Exception:
        return "not ok"
app.add_url_rule('/assign_task', 'assign_task', assign_task)

def kill_thread():
    """assign kill thread as True
    """
    global kill_flag
    print('-------------- kill flag')
    print(kill_flag)
    kill_flag = True
    return "ok"
app.add_url_rule('/kill_thread', 'kill_thread', kill_thread)

def init_folder():
    """
    Initialize folders ``local`` and ``local_responsibility``, prepare ``local_children`` and ``local_mapping`` file.
    
    Raises:
        Exception: ``ok`` if successful, ``not ok`` otherwise
    """
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


def recv_control():
    """Get assigned control function, prepare file ``DAG/parent_controller.txt`` storing parent control information of tasks 
    
    Raises:
        Exception: ``ok`` if successful, ``not ok`` otherwise
    """
    try:
        print('Get assigned control function -----------------------')
        control = request.args.get('control')
        items = re.split(r'#', control)
        print(items)

        to_be_write = []
        for _, item in enumerate(items):
            print(item)
            to_be_write.append(item.replace("__", "\t"))
            print(to_be_write)
            tmp = re.split(r"__", item)
            print(tmp)
            key = tmp[0]
            del tmp[0]
            control_relation[key] = tmp
            print(control_relation)

        if not os.path.exists("./DAG"):
            print('No folder DAG')
            os.mkdir("./DAG")

        print(to_be_write)
        print('DAG/parent_controller.txt')
        write_file("DAG/parent_controller.txt", to_be_write, "a+")
    except Exception:
        return "not ok"
    return "ok"
app.add_url_rule('/recv_control', 'recv_control', recv_control)

def assign_task_to_remote(assigned_node, task_name):
    """Assign task to remote node
    
    Args:
        - assigned_node (str): Node to be assigned
        - task_name (str): task name 
    
    Raises:
        Exception: request if successful, ``not ok`` if failed
    """
    try:
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
        url = "http://" + master_host + "/recv_mapping"
        params = {'mapping': mapping, "node": node}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        return "not ok"
    return res



def watcher():
    """- thread to watch directory: ``local/task_responsibility``
       - Write tasks to ``local/local_children.txt`` and ``local/local_mapping.txt`` that appear under the watching folder
    """
    pre_time = time.time()

    tmp_mapping = ""
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print(kill_flag)
    while True:
        if kill_flag:
            break
        print('$$$$$$$$$$$$$$$$$$$$$$$$$$3')
        if not os.path.exists(local_responsibility):
            time.sleep(1)
            continue
        print('$$$$$$$$$$$$$$$$$$$$$$$$$$4')
        tasks = scan_dir(local_responsibility)
        output("Find tasks under task_responsibility: " + json.dumps(tasks))
        for _, task in enumerate(tasks):
            print(tasks)
            print(task)
            print(control_relation)
            print('$$$$$$$$$$$$$$$$$$$$$$$$$5')
            if task in control_relation.keys():
                print(task)
                controlled = control_relation[task]
                print(controlled)
                for _, t in enumerate(controlled):
                    print('$$$$$$$$$$$$$$$$$$$$$$6')
                    print(t)
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



def distribute():
    """thread to assign todo task to remote nodes
    """
    done_dict = set()
    start = int(time.time())

    # wait for network_profile_data and resource_data be ready
    while True:
        if is_network_profile_data_ready and is_resource_data_ready:
            break
        else:
            print("Waiting for the profiler data")
            time.sleep(100)

    print(kill_flag)
    while True:
        if kill_flag:
            break

        if not os.path.exists(local_children):
            time.sleep(1)
            continue

        lines = read_file(local_children)
        print('**********')
        print(lines)
        for line in lines:
            line = line.strip()
            print(line)
            if "TODO" in line:
                output("Find todo item: " + line)

                items = re.split(r'\t+', line)
                if items[0] in done_dict:
                    print(items[0], "already assigned")
                    continue

                assign_to_node = get_most_suitable_node(len(items[0]))
                if not assign_to_node:
                    print("No suitable node found for assigning task: ", items[0])
                    continue

                print("Trying to assign", items[0], "to", assign_to_node)
                status = assign_task_to_remote(assign_to_node, items[0])
                if status == "ok":
                    assign_info = {
                        'node_id': assign_to_node,
                        'task': items[0],
                        'time': time.time()
                    }
                    output(str(assign_info))

                    summary_info = 'node_name: %s, task: %s, time: %s' % \
                                   (assign_to_node, items[0], str(time.time()))
                    send_task_assign_info_to_master(summary_info)

                    done_dict.add(items[0])
                else:
                    output("Assign " + items[0] + " to " + assign_to_node + " failed")

        time.sleep(10)


def send_task_assign_info_to_master(info):
    """send summary of task assignment info to master node and print
    
    Args:
        info (str): node information
    """
    try:
        tmp_home_ip = os.environ['HOME_IP']
        url = "http://" + tmp_home_ip + ":" + str(FLASK_SVC) + "/recv_task_assign_info?assign=" + info
        resp = requests.get(url).text
        if resp == "ok":
            output('Send task assign info to master succeeded')
            return
    except Exception as e:
        print("Send task assign info to master, details: " + str(e))

    output('Send task assign info to master failed')

def get_most_suitable_node(size):
    """Calculate network delay + resource delay
    
    Args:
        size (int): file size
    
    Returns:
        str: result_node_name - assigned node for the current task
    """
    weight_network = 1
    weight_cpu = 1
    weight_memory = 1

    valid_nodes = []

    min_value = sys.maxsize

    for tmp_node_name in network_profile_data:
        data = network_profile_data[tmp_node_name]
        delay = data['a'] * size * size + data['b'] * size + data['c']
        network_profile_data[tmp_node_name]['delay'] = delay
        if delay < min_value:
            min_value = delay

    # get all the nodes that satisfy: time < tmin * threshold
    for _, item in enumerate(network_profile_data):
        if network_profile_data[item]['delay'] < min_value * threshold:
            valid_nodes.append(item)

    min_value = sys.maxsize
    result_node_name = ''
    for item in valid_nodes:
        print(item)
        tmp_value = network_profile_data[item]['delay']

        tmp_cpu = 10000
        tmp_memory = 10000
        if item in resource_data.keys():
            print(resource_data[item])
            tmp_cpu = resource_data[item]['cpu']
            tmp_memory = resource_data[item]['memory']

        tmp_cost = weight_network*tmp_value + weight_cpu*tmp_cpu + weight_memory*tmp_memory
        if  tmp_cost < min_value:
            min_value = tmp_cost
            result_node_name = item

    if not result_node_name:
        min_value = sys.maxsize
        for item in resource_data:
            tmp_cpu = resource_data[item]['cpu']
            tmp_memory = resource_data[item]['memory']
            tmp_cost = weight_cpu*tmp_cpu + weight_memory*tmp_memory
            if  tmp_cost < min_value:
                min_value = tmp_cost
                result_node_name = item

    if result_node_name:
        network_profile_data[result_node_name]['c'] = 100000

    return result_node_name


def scan_dir(directory):
    """Scan the directory, append all file names to list ``tasks``
    
    Args:
        directory (str): directory path
    
    Returns:
        list: tasks - List of all file names in the directory
    """
    tasks = []
    for file_name in os.listdir(directory):
        tasks.append(file_name)
    return tasks


def create_file():
    """Do nothing/ pass
    """
    pass


def write_file(file_name, content, mode):
    """Write the content to file
    
    Args:
        - file_name (str): file path
        - content (str): content to be written
        - mode (str): write mode 
    """
    print('Wrting file process ------------------')
    print(file_name)
    print(content)
    print(mode)
    print(lock)
    lock.acquire()
    file = open(file_name, mode)
    for line in content:
        file.write(line + "\n")
    file.close()
    lock.release()
    print('Ending Wrting file process ------------------')


def read_file(file_name):
    """get all lines in a file
    
    Args:
        file_name (str): file path
    
    Returns:
        str: file_contents - all lines in a file
    """

    lock.acquire()
    file_contents = []
    file = open(file_name)
    line = file.readline()
    while line:
        file_contents.append(line)
        line = file.readline()
    file.close()
    lock.release()
    print('@@@@@@@@@@@')
    print(file_contents)
    return file_contents


def output(msg):
    """if debug is True, print the msg
    
    Args:
        msg (str): message to be printed
    """
    if debug:
        print(msg)


def get_resource_data_drupe():
    """Collect resource profiling information
    """
    print("Starting resource profile collection thread")
    # Requsting resource profiler data using flask for its corresponding profiler node
    try_resource_times = 0
    while True:
        time.sleep(60)
        try:
            if try_resource_times >= 10:
                print("Exceeded maximum try times, break.")
                break
            r = requests.get("http://" + os.environ['PROFILER'] + ":" + str(FLASK_SVC) + "/all")
            result = r.json()
            print(result)
            if len(result) != 0:
                break
            else:
                try_resource_times += 1
        except Exception as e:
            print("Resource request failed. Will try again, details: " + str(e))
            try_resource_times += 1
    global resource_data
    resource_data = result

    global is_resource_data_ready
    is_resource_data_ready = True

    print("Got profiler data from http://" + os.environ['PROFILER'] + ":" + str(FLASK_SVC))
    print("Resource profiles: ", json.dumps(result))


def get_network_data_drupe(my_profiler_ip, MONGO_SVC_PORT, network_map):
    """Collect the network profile from local MongoDB peer
    """
    print('Check My Network Profiler IP: '+my_profiler_ip)
    client_mongo = MongoClient('mongodb://'+my_profiler_ip+':'+MONGO_SVC_PORT+'/')
    db = client_mongo.droplet_network_profiler
    collection = db.collection_names(include_system_collections=False)
    print(collection)
    num_nb = len(collection)-1
    while num_nb==-1:
        print('--- Network profiler mongoDB not yet prepared')
        time.sleep(60)
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
    print('--- Number of neighbors: '+str(num_nb))
    num_rows = db[my_profiler_ip].count()
    print(num_rows)
    while num_rows < num_nb:
        print('--- Network profiler regression info not yet loaded into MongoDB!')
        time.sleep(60)
        num_rows = db[my_profiler_ip].count()
    logging =db[my_profiler_ip].find().limit(num_nb)
    print(logging)
    print('^^^^^^^^^^^^^^^')
    print(network_map)
    for record in logging:
        print('&&&&&&&&&&&&')
        print(record)
        # Destination ID -> Parameters(a,b,c) , Destination IP
        print(home_profiler_ip)
        print(record['Destination[IP]'])
        if record['Destination[IP]'] == home_profiler_ip: continue
        params = re.split(r'\s+', record['Parameters'])
        print(params)
        network_profile_data[network_map[record['Destination[IP]']]] = {'a': float(params[0]), 'b': float(params[1]),
                                                            'c': float(params[2]), 'ip': record['Destination[IP]']}
    print('Network information has already been provided')
    print(network_profile_data)

    global is_network_profile_data_ready
    is_network_profile_data_ready = True



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

    global node_name, node_id, FLASK_PORT, home_profiler_ip

    node_name = os.environ['SELF_NAME']
    node_id = int(node_name.split("e")[-1])
    home_profiler_ip = os.environ['HOME_PROFILER_IP']

    print("Node name:", node_name, "and id", node_id)
    print("Starting the main thread on port", FLASK_PORT)

    
    get_network_data = get_network_data_mapping()
    get_resource_data = get_resource_data_mapping()
    while init_folder() != "ok":  # Initialize the local folers
        pass

    # Get resource data
    _thread.start_new_thread(get_resource_data, ())

    # Get network profile data
    _thread.start_new_thread(get_network_data, (my_profiler_ip, MONGO_SVC_PORT,network_map))

    _thread.start_new_thread(watcher, ())
    _thread.start_new_thread(distribute, ())

    app.run(host='0.0.0.0', port=int(FLASK_PORT))


if __name__ == '__main__':
    main()
    
