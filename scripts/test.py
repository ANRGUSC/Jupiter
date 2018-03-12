import timeit
import os
from os import path
import sys, json
import paramiko
import time
from scp import SCPClient
from socket import gethostbyname, gaierror
import requests
import subprocess
import pyinotify
from pymongo import MongoClient
import pandas as pd
import _thread
import datetime


NUM_NODES = 89 #TODO: env 
class MyEventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        print("New execution profiler files created:", event.pathname)
        file_name = os.path.basename(event.pathname)
        node_info = file_name.split('_')[1]
        node_info = node_info.split('.')[0]
        print("Node info: ", node_info )
        client_mongo = MongoClient('mongodb://localhost:27017/')
        db = client_mongo['execution_profiler']
        db.create_collection(node_info)
        logging = db[node_info]
        with open(event.pathname) as f:
            first_line = f.readline()
            print(first_line)
            for line in f:
                parts = line.split()
                print(parts)
            try:
                df = pd.read_csv(event.pathname,delimiter=',',header=0,names = ["Task","Duration [sec]", "Output File [Kbit]"])
                data_json = json.loads(df.to_json(orient='records'))
                logging.insert(data_json)
                print('MongodB Update Successful')
            except Exception as e:
                print('MongoDB error')
                print(e)

def update_mongo(self,file_path):
    file_name = os.path.basename(file_path)
    node_info = file_name.split('_')[1]
    node_info = node_info.split('.')[0]
    print("Node info: ", node_info )
    client_mongo = MongoClient('mongodb://localhost:27017/')
    db = client_mongo['execution_profiler']
    db.collection.remove(node_info)
    db.create_collection(node_info)
    logging = db[node_info]
    with open(file_path) as f:
        first_line = f.readline()
        print(first_line)
        for line in f:
            parts = line.split()
            print(parts)
        try:
            df = pd.read_csv(file_path,delimiter=',',header=0,names = ["Task","Duration [sec]", "Output File [Kbit]"])
            data_json = json.loads(df.to_json(orient='records'))
            logging.insert(data_json)
            print('MongodB Update Successful')
        except Exception as e:
            print('MongoDB error')
            print(e)    

def convert_bytes(num):
        """ Convert bytes to Kbit as required by HEFT"""

        # for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        #     if num < 1024.0:
        #         return "%3.1f %s" % (num, x)
        #     num /= 1024.0
        return num*0.008

def file_size(file_path):
    """ Return the file size in bytes """

    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)


if __name__ == '__main__':

    configs = json.load(open('/centralized_scheduler/config.json'))
    dag_flag = configs['exec_profiler']
    task_map = configs['taskname_map']

    nodename = 'home'
    print(nodename)

    client_mongo = MongoClient('mongodb://localhost:27017/')
    db = client_mongo['execution_profiler']
    
    local_profiler_path    = os.path.join(os.path.dirname(__file__), 'profiler_files/')
    nonDAG_file = local_profiler_path+ 'profiler_home.txt'
    print(nonDAG_file)
    print('update non DAG info in MongoDB')
    client_mongo = MongoClient('mongodb://localhost:27017/')
    db = client_mongo['execution_profiler']
    db.collection.remove('home')
    db.create_collection('home')
    logging = db['home']
    with open(nonDAG_file) as f:
        first_line = f.readline()
        print(first_line)
        for line in f:
            parts = line.split()
            print(parts)
        try:
            df = pd.read_csv(nonDAG_file,delimiter=',',header=0,names = ["Task","Duration [sec]", "Output File [Kbit]"])
            data_json = json.loads(df.to_json(orient='records'))
            logging.insert(data_json)
            print('MongodB Update Successful')
        except Exception as e:
            print('MongoDB error')
            print(e)


    num_profiling_files = 0
    profiling_folder = '/centralized_scheduler/profiler_files/'
    while num_profiling_files < NUM_NODES:
        list_files = os.listdir(profiling_folder) # dir is your directory path
        num_profiling_files = len(list_files)
        print("Number of execution profiling files : " + str(num_profiling_files))
        time.sleep(60)

    for file_path in list_files:
        print('--- Add execution info from file: '+ file_path)
        update_mongo(file_path)

