"""
.. note:: This is the main script to run in every node in the system for resource profiling procedure.
"""
__author__ = "Jiatong Wang, Pranav Sakulkar, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

from flask import Flask
import psutil
import json
import time
import os
import _thread
import threading
import datetime
import requests
import configparser
from os import path



def monitor_neighbours():
    """
    Obtain all resources stats as JSON format from all of the nodes in the network every minute.
    """
    while True:
        time.sleep(60) # Profile all_resources every minute

        print("Monitoring all_resources for neighbors")

        for node_ip, node_name in zip(IPs, node_names):
            if node_ip == "":
                continue

            print("Probing Node IP:", node_ip)
            if node_ip == os.environ['SELF_IP']:
                with lock:
                    local = dict(local_resources)
                with all_lock:
                    all_resources[node_name] = local
                continue

            print("Grab local resource data from http://"+node_ip+ ":" + str(FLASK_SVC))
            r = requests.get("http://"+node_ip+":" + str(FLASK_SVC))
            result = r.json()
            if not result:
                print("Request result empty from", node_name)
                continue

            with all_lock:
                all_resources[node_name] = result

        print("Local copy of All resources")
        with all_lock:
            print(all_resources)

def monitor_local_resources():
    """
    Obtain local resource stats(CPU, Memory usage and the lastest timestamp) from local node and store it to the variable `local_resources`
    """
    global local_resources
    while True:
        print('Updating local resource stats')
        with lock:
            res = dict(local_resources)
        res["memory"] = (psutil.virtual_memory().percent + res['memory'] * res['count']) / (res['count'] + 1)
        res["cpu"] = (psutil.cpu_percent() + res['cpu'] * res['count']) / (res['count'] + 1)
        res['count'] += 1
        res['last_update'] = datetime.datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')

        with lock:
            local_resources = res
        time.sleep(60) # Profile variables every minute

#@app.route('/') # Send local stats
def performance():
    print("Responding to the loal resource performance request")
    with lock:
        print(local_resources)
        js = json.dumps(local_resources)
    return js
app.add_url_rule('/', 'performance', performance)

#@app.route('/all') # Send all stats
def all_performance():
    with all_lock:
        if len(all_resources) == len(IPs) - 1:
            print("Sending resource stats for all neighbors")
            print(all_resources)
            js = json.dumps(all_resources)
        else:
            print("Not all neighbor stats are received")
            js = json.dumps({})
    return js
app.add_url_rule('/all', 'all_performance', all_performance)

def main():
    """
        - ``all_resources`` : Storage for observations for all_resources
        - Key is the IP address and value is the dictionary of resouces for that IP
        - Start a thread obtain and store the local stats
        - Start a thread to monitor resouces of all the nodes in the network and store their stats
    """

    # Load all the confuguration
    INI_PATH = '/network_profiling/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])
    FLASK_SVC    = int(config['PORT']['FLASK_SVC'])
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])

    app = Flask(__name__)

    all_resources = {} #Storage for observations for all_resources
    # Key is the IP address and value is the dictionary of resouces for that IP

    local_resources = {'memory': 0.0, 'cpu': 0.0, 'count': 1}

    lock = threading.Lock()
    all_lock = threading.Lock()

    IPs = os.environ['ALL_NODES_IPS'].split(":")
    node_names = os.environ['ALL_NODES'].split(":")

    print("Starting the Flask Server")
    # Start the thread for storing the local stats for all neibhors
    _thread.start_new_thread(monitor_neighbours, ())

    # Start a thread to monitor local resouces and store their stats
    _thread.start_new_thread(monitor_local_resources, ())

    app.run(host='0.0.0.0', port=FLASK_DOCKER) #run this web application on 0.0.0.0 and default port is 5000

if __name__ == '__main__':
    main()
