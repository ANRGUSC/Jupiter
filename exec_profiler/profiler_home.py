"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh
 *      Quynh Nguyen
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""

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

def update_mongo(file_path):
    file_name = os.path.basename(file_path)
    node_info = file_name.split('_')[1]
    node_info = node_info.split('.')[0]
    print("Node info: ", node_info )
    client_mongo = MongoClient('mongodb://localhost:27017/')
    db = client_mongo['execution_profiler']
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


    #create the task list in the order of execution
    task_order = []
    tasks_info = open(os.path.join(os.path.dirname(__file__), 'DAG.txt'), "r")

    #create DAG dictionary
    tasks = {}
    count = 0
    for line in tasks_info:
        if count == 0:
            count += 1
            continue

        data = line.strip().split(" ")
        if task_map[data[0]][1] == False:
            continue

        tasks.setdefault(data[0], [])
        if data[0] not in task_order:
            task_order.append(data[0])
        for i in range(3, len(data)):
            if  data[i] != 'home' and task_map[data[i]][1] == True :
                tasks[data[0]].append(data[i])
    print("tasks: ", tasks)

    #import task modules, put then in a list and create task-module dictinary
    task_module = {}
    modules=[]
    for task in tasks.keys():
        print(task)
        os.environ['TASK'] = task
        taskmodule  = __import__(task)
        modules.append(taskmodule)
        task_module[task]=(taskmodule)

    #print('{0:<16s} {1:<15s} {2:<5s} \n'.format('task', 'time (sec)', 'output_data (Kbit)'))
    #write results in a text file
    myfile = open(os.path.join(os.path.dirname(__file__), 'profiler_'+nodename+'.txt'), "w")
    myfile.write('task,time(sec),output_data (Kbit)\n')
    print(task_order)

    #execute each task and get the timing and data size
    for task in task_order:

        module = task_module.get(task)
        os.environ['TASK'] = task
        print(task)

        start_time = datetime.datetime.utcnow()
        filename = module.main()
        stop_time = datetime.datetime.utcnow()
        mytime = stop_time - start_time
        mytime = int(mytime.total_seconds()) #convert to seconds

        output_data = [file_size(fname) for fname in filename]
        sum_output_data = sum(output_data) #current: summation of all output files
        line=task+','+str(mytime)+ ','+ str(sum_output_data) + '\n'
        print(line)
        myfile.write(line)
        myfile.flush()



    myfile.close()

    print('Finish printing out the execution information')
    print('Starting to send the output file back to the master node')


    # TODO: send the intermedaiate files to the remote location
    # TODO: send a signal to the k8 to remove the nonDAG tasks
    #

    #
    #send output file back to the scheduler machine
    # master_IP        = os.environ['HOME_NODE']
    # username            = 'root'   # TODO: Have hardcoded for now. But will change later
    # password            = 'PASSWORD'
    # ssh_port            = 5000
    # num_retries         = 20
    # retry               = 0

    # dir_remote          = '/profiler_files'
    # node_name           = os.environ['NODE_NAME']
    print('Copy supertask information to profilers folder')
    master_profile_file_name = os.path.join(os.path.dirname(__file__), 'profiler_' + nodename + '.txt')
    local_profiler_path    = os.path.join(os.path.dirname(__file__), 'profiler_files/')
    if path.isfile(master_profile_file_name):
        os.system('mv ' + master_profile_file_name + ' ' + local_profiler_path)

    nonDAG_file = local_profiler_path+ 'profiler_home.txt'
    print(nonDAG_file)
    print('update non DAG info in MongoDB')
    client_mongo = MongoClient('mongodb://localhost:27017/')
    db = client_mongo['execution_profiler']

    profilers_ips = os.environ['ALL_PROFILERS_IPS'].split(':')
    allprofiler_names = os.environ['ALL_PROFILERS_NAMES'].split(':')
    ptFile = "/centralized_scheduler/generated_files/"
    ptFile1 = "/centralized_scheduler/"


    RP_PORT = 48888

    for itr in range(1, len(profilers_ips)):
        i = profilers_ips[itr]
        cmd = "sshpass -p 'PASSWORD' scp -P 5100 -o StrictHostKeyChecking=no -r %s %s:%s" % (ptFile, i, ptFile1)
        print("Sending data to ", allprofiler_names[itr])
        os.system(cmd)

        try:
            print("start the profiler in ", i)
            r = requests.get("http://"+i+":" + str(RP_PORT))
            result = r.json()
        except:
            print("Some Exception")

    print('Watching the incoming execution profiler files')
    # watch manager
    # wm = pyinotify.WatchManager()
    # wm.add_watch('/centralized_scheduler/profiler_files', pyinotify.ALL_EVENTS, rec=True)
    # # event handler
    # eh = MyEventHandler()
    # # notifier
    # notifier = pyinotify.Notifier(wm, eh)
    # notifier.loop()
    num_profiling_files = 0
    profiling_folder = '/centralized_scheduler/profiler_files'
    while num_profiling_files < NUM_NODES:
        list_files = os.listdir(profiling_folder) # dir is your directory path
        num_profiling_files = len(list_files)
        print("Number of execution profiling files : " + str(num_profiling_files))
        time.sleep(60)

    for file_path in list_files:
        print('--- Add execution info from file: '+ file_path)
        pathh = profiling_folder + '/' + file_path
        update_mongo(pathh)

