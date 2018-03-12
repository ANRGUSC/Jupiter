"""
 ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 **     contributor: Quynh Nguyen, Aleksandra Knezevic, Bhaskar Krishnamachari
 **     Read license file in main directory for more details
"""

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
# from node_info import *
print("starting the main thread on port")

app = Flask(__name__)

'''
'''

network_info = []
execution_info = []
debug = True

def output(msg):
    if debug:
        print(msg)

def get_global_info():
    MONGO_PORT = '6200'
    profiler_ip = os.environ['PROFILERS'].split(' ')
    profiler_ip = [info.split(":") for info in profiler_ip]
    exec_home_ip = os.environ['EXECUTION_HOME_IP']
    num_nodes = len(profiler_ip)
    print(num_nodes)
    node_list = [info[0] for info in profiler_ip]
    node_IP = [info[1] for info in profiler_ip]
    network_map = dict(zip(node_IP, node_list))
    return profiler_ip,exec_home_ip,num_nodes,MONGO_PORT,network_map,node_list

def get_exec_profile_data(exec_home_ip, MONGO_PORT, num_nodes):

    # Collect the execution profile from the home execution profiler's MongoDB
    num_profilers = 0
    conn = False
    while not conn:
        try:
            client_mongo = MongoClient('mongodb://'+exec_home_ip+':'+MONGO_PORT+'/')
            db = client_mongo.execution_profiler
            conn = True
        except:
            print('Error connection')
            time.sleep(60)

    print(db)
    while num_profilers < (num_nodes+1):
        try:
            collection = db.collection_names(include_system_collections=False)
            num_profilers = len(collection)
            print(num_profilers)
        except Exception as e:
            print('--- Execution profiler info not yet loaded into MongoDB!')
            time.sleep(60)

    #print(collection)
    for col in collection:
        print('--- Check execution profiler ID : '+ col)
        logging =db[col].find()
        for record in logging:
            # Node ID, Task, Execution Time, Output size
            info_to_csv=[col,record['Task'],record['Duration [sec]'],str(record['Output File [Kbit]'])]
            execution_info.append(info_to_csv)
    output('Execution information has already been provided')
    # print(execution_info)
    with open('/heft/execution_log.txt','w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(execution_info)
    return

def get_network_profile_data(profiler_ip, MONGO_PORT, network_map):
    # Collect the network profile from local MongoDB peer
    output(profiler_ip)
    for ip in profiler_ip:
        print('Check Network Profiler IP: '+ip[0]+ '-' +ip[1])
        client_mongo = MongoClient('mongodb://'+ip[1]+':'+MONGO_PORT+'/')
        db = client_mongo.droplet_network_profiler
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection)-1
        while num_nb==-1:
            print('--- Network profiler mongoDB not yet prepared')
            time.sleep(60)
            collection = db.collection_names(include_system_collections=False)
            num_nb = len(collection)-1
        output('--- Number of neighbors: '+str(num_nb))
        num_rows = db[ip[1]].count()
        while num_rows < num_nb:
            print('--- Network profiler regression info not yet loaded into MongoDB!')
            time.sleep(60)
            num_rows = db[ip[1]].count()
        logging =db[ip[1]].find().limit(num_nb)
        for record in logging:
            # print(record)
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            info_to_csv=[network_map[record['Source[IP]']],record['Source[IP]'],network_map[record['Destination[IP]']], record['Destination[IP]'],str(record['Parameters'])]
            network_info.append(info_to_csv)
    output('Network information has already been provided')
    #print(network_info)
    with open('/heft/network_log.txt','w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(network_info)
    return

if __name__ == '__main__':


    print('---------------------------------------------')
    print('\n Step 1: Read task list from DAG file and global information \n')

    configuration_path='/heft/dag.txt'
    profiler_ip,exec_home_ip,num_nodes,MONGO_PORT,network_map,node_list = get_global_info()
    output(profiler_ip)
    output(exec_home_ip)
    output("Num nodes :" + str(num_nodes))
    output(network_map)
    output(node_list)

    print('------------------------------------------------------------')
    print("\n Step 2: Read network profiler information : \n")
    _thread.start_new_thread(get_network_profile_data, (profiler_ip, MONGO_PORT,network_map))

    print('------------------------------------------------------------')
    print("\n Step 3: Read execution Profiler Information : \n")
    _thread.start_new_thread(get_exec_profile_data, (exec_home_ip, MONGO_PORT,num_nodes))

    while True:
        time.sleep(120)