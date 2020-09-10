#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
   This file read the generated TGFF file as an input of HEFT
"""
__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import pymongo
from pymongo import MongoClient
import pandas as pd
import json
import glob
import _thread
import time
from create_input import init
import sys
from flask import Flask, request
import csv
import configparser
from os import path
from functools import wraps
import paho.mqtt.client as mqtt


app = Flask(__name__)

'''
'''

network_info = []
execution_info = []


def demo_help(server,port,topic,msg):
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()

def get_global_info():
    """Get all information of profilers (network profilers, execution profilers)
    
    Returns:
        -   list: profiler_ip - IPs of network profilers
        -   list: exec_home_ip - IPs of execution profilers
        -   int:  num_nodes - number of nodes
        -   str:  MONGO_SVC_PORT - Mongo service port
        -   dict: network_map - mapping of node IPs and node names
        -   dict: node_list - node list
    """
    global profiler_ip,exec_home_ip,num_nodes,MONGO_SVC_PORT,network_map,node_list, home_profiler_ip, home_profiler_nodes
    profiler_ip = os.environ['PROFILERS'].split(' ')
    profiler_ip = [info.split(":") for info in profiler_ip]
    exec_home_ip = os.environ['EXECUTION_HOME_IP']
    num_nodes = len(profiler_ip)
    node_list = [info[0] for info in profiler_ip]
    node_IP = [info[1] for info in profiler_ip]
    network_map = dict(zip(node_IP, node_list))
    home_profiler = os.environ['HOME_PROFILER_IP'].split(' ')
    home_profiler_nodes = [x.split(':')[0] for x in home_profiler]
    home_profiler_ip = [x.split(':')[1] for x in home_profiler]


    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

def get_exec_profile_data(exec_home_ip, MONGO_SVC_PORT, num_nodes):
    """Collect the execution profile from the home execution profiler's MongoDB
    
    Args:
        - exec_home_ip (str): IP of execution profiler home
        - MONGO_SVC_PORT (str): Mongo service port
        - num_nodes (int): number of nodes
    """

    num_profilers = 0
    conn = False
    while not conn:
        try:
            client_mongo = MongoClient('mongodb://'+exec_home_ip+':'+MONGO_SVC_PORT+'/')
            db = client_mongo.execution_profiler
            conn = True
        except:
            print('Error connection')
            time.sleep(60)

    while num_profilers < (num_nodes+1):
        try:
            collection = db.collection_names(include_system_collections=False)
            num_profilers = len(collection)
        except Exception as e:
            print('--- Execution profiler info not yet loaded into MongoDB!')
            time.sleep(60)

    for col in collection:
        if col in home_profiler_nodes:
            continue
        logging =db[col].find()
        for record in logging:
            # Node ID, Task, Execution Time, Output size
            info_to_csv=[col,record['Task'],record['Duration [sec]'],str(record['Output File [Kbit]'])]
            execution_info.append(info_to_csv)
    print('--------------------------------------------')
    print('Execution information has already been provided')
    with open('/heft/execution_log.txt','w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(execution_info)

    if BOKEH==3:
        n = num_profilers*len(logging)
        msg = 'msgoverhead balancehefthome resourcedata %d\n'%(n)
        demo_help(BOKEH_SERVER,BOKEH_PORT,"msgoverhead_home",msg)
    return


def profilers_mapping_decorator(f):
    """General Profilers Mapping function
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

def get_network_data_drupe(profiler_ip, MONGO_SVC_PORT, network_map):
    """Collect the network profile from local MongoDB peer
    
    Args:
        - profiler_ip (list): IPs of network profilers
        - MONGO_SVC_PORT (str): Mongo service port
        - network_map (dict): mapping of node IPs and node names
    """
    for ip in profiler_ip:
        print('Check Network Profiler IP: '+ip[0]+ '-' +ip[1])
        client_mongo = MongoClient('mongodb://'+ip[1]+':'+MONGO_SVC_PORT+'/')
        db = client_mongo.droplet_network_profiler
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
        while num_nb==-1:
            print('--- Network profiler mongoDB not yet prepared')
            time.sleep(60)
            collection = db.collection_names(include_system_collections=False)
            num_nb = len(collection)-1
        num_rows = db[ip[1]].count()
        while num_rows < num_nb:
            print('--- Network profiler regression info not yet loaded into MongoDB!')
            time.sleep(60)
            num_rows = db[ip[1]].count()
        logging = db[ip[1]].find().skip(db.collection.count() - num_nb)
    
        for record in logging:
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            if record['Destination[IP]'] in home_profiler_ip: 
                continue
            info_to_csv=[network_map[record['Source[IP]']],record['Source[IP]'],network_map[record['Destination[IP]']], record['Destination[IP]'],str(record['Parameters'])]
            network_info.append(info_to_csv)
    print('Network information has already been provided')
    with open('/heft/network_log.txt','w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(network_info)

    if BOKEH==3:
        n = len(profiler_ip)*num_nb
        msg = 'msgoverhead balancehefthome networkdata %d\n'%(n)
        demo_help(BOKEH_SERVER,BOKEH_PORT,"msgoverhead_home",msg)
    return

if __name__ == '__main__':
    """
        - Load all the confuguration
        - Read task list from DAG file and global information
        - Read network profiler information
        - Read execution Profiler Information
    """

    ## Load all the configuration
    HERE     = path.abspath(path.dirname(__file__)) + "/"
    INI_PATH = HERE + 'jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global EXC_FPORT, MONGO_SVC_PORT
    
    EXC_FPORT = int(config['PORT']['FLASK_SVC'])
    MONGO_SVC_PORT = config['PORT']['MONGO_SVC']


    global PROFILER
    PROFILER = int(config['CONFIG']['PROFILER'])

    print('---------------------------------------------')
    print('\n Step 1: Read task list from DAG file and global information \n')

    configuration_path='/heft/dag.txt'
    global profiler_ip,exec_home_ip,num_nodes,network_map,node_list
    get_global_info()

    print('------------------------------------------------------------')
    print("\n Step 2: Read network profiler information : \n")

    get_network_data = get_network_data_mapping()
    
    _thread.start_new_thread(get_network_data, (profiler_ip, MONGO_SVC_PORT,network_map))

    print('------------------------------------------------------------')
    print("\n Step 3: Read execution Profiler Information : \n")
    _thread.start_new_thread(get_exec_profile_data, (exec_home_ip, MONGO_SVC_PORT,num_nodes))

    while True:
        time.sleep(120)
