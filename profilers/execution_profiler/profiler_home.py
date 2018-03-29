__author__ = "Pradipta Ghosh, Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

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
import shutil
import configparser


class MyEventHandler(pyinotify.ProcessEvent):

    """Handling the event when new execution profiler files are generated
    """
    
    def process_IN_CLOSE_WRITE(self, event):
        """Write execution profiling information into local MongoDB database
        
        Args:
            event (str): New execution profiler files created
        """
        print("New execution profiler files created:", event.pathname)
        file_name = os.path.basename(event.pathname)
        node_info = file_name.split('_')[1]
        node_info = node_info.split('.')[0]
        print("Node info: ", node_info )
        client_mongo = MongoClient('mongodb://localhost:'+ str(MONGO_PORT) +'/')
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
    """Update the MongoDb with the data from the Execution profiler
    
    Args:
        file_path (str): The file path 
    """
    file_name = os.path.basename(file_path)
    node_info = file_name.split('_')[1]
    node_info = node_info.split('.')[0]
    print("Node info: ", node_info )
    client_mongo = MongoClient('mongodb://localhost:'+ str(MONGO_PORT) +'/')
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
    """Convert bytes to Kbit as required by HEFT
    
    Args:
        num (int): The number of bytes
    
    Returns:
        float: file size in Kbits
    """
    return num*0.008

def file_size(file_path):
    """Return the file size in bytes
    
    Args:
        file_path (str): The file path
    
    Returns:
        float: file size in bytes
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)



def main():
    """
        -   Load all the confuguration
        -   create the task list in the order of execution
        -   execute each task and get the timing and data size
        -   send intermediate files to the worker execution profilers
        -   Transfer the Intermdiate Files To all the Workers.
        -   Start Waiting For Incoming Statistics from the Worker Execution Profilers. Once a File arrives at the ``profiling_folder`` immediately process it and move it to the ``profiling_folder_processed`` to keep track of processed files
    """
    ## Load all the confuguration
    HERE     = path.abspath(path.dirname(__file__)) + "/"
    INI_PATH = HERE + 'jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    EXC_FPORT = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT = int(config['PORT']['MONGO_DOCKER'])

    configs = json.load(open('/centralized_scheduler/config.json'))
    dag_flag = configs['exec_profiler']
    task_map = configs['taskname_map']

    nodename = 'home'
    print(nodename)

    client_mongo = MongoClient('mongodb://localhost:'+ str(MONGO_PORT) +'/')
    db = client_mongo['execution_profiler']


    ## create the task list in the order of execution
    task_order = []
    tasks_info = open(os.path.join(os.path.dirname(__file__), 'DAG.txt'), "r")

    ## create DAG dictionary
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

    ## import task modules, put then in a list and create task-module dictinary
    task_module = {}
    modules=[]
    for task in tasks.keys():
        print(task)
        os.environ['TASK'] = task
        taskmodule  = __import__(task)
        modules.append(taskmodule)
        task_module[task]=(taskmodule)

    ## write results in a text file
    myfile = open(os.path.join(os.path.dirname(__file__), 'profiler_'+nodename+'.txt'), "w")
    myfile.write('task,time(sec),output_data (Kbit)\n')
    print(task_order)

    ## execute each task and get the timing and data size
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

    ## send intermediate files to the worker execution profilers
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = 20
    retry       = 0


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
    client_mongo = MongoClient('mongodb://localhost:'+ str(MONGO_PORT) +'/')
    db = client_mongo['execution_profiler']

    profilers_ips = os.environ['ALL_PROFILERS_IPS'].split(':')
    allprofiler_names = os.environ['ALL_PROFILERS_NAMES'].split(':')
    ptFile = "/centralized_scheduler/generated_files/"
    ptFile1 = "/centralized_scheduler/"


    """
        Transfer the Intermdiate Files Tt all the Workers. 
        TODO?? Use Paramiko or similar tool instead of the commandline scp
    """
    for itr in range(1, len(profilers_ips)):
        i = profilers_ips[itr]
        cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s:%s" % (password, ssh_port, ptFile, i, ptFile1)
        print("Sending data to ", allprofiler_names[itr])
        os.system(cmd)

        try:
            print("start the profiler in ", i)
            r = requests.get("http://"+i+":" + str(EXC_FPORT))
            result = r.json()
        except:
            print("Some Exception")




    ## Start Waiting For Incoming Statistics from the Worker Execution Profilers
    ## Once a File arrives at the profiling_folder immediately process it and
    ## move it to the profiling_folder_processed to keep track of processed files

    print('Watching the incoming execution profiler files')
    num_profiling_files = 0
    profiling_folder = '/centralized_scheduler/profiler_files'
    profiling_folder_processed = '/centralized_scheduler/profiler_files_processed/'

    recv_file_count = 0
    while 1:

        list_files = os.listdir(profiling_folder) # dir is your directory path

        for file_path in list_files:
            try:
                print('--- Add execution info from file: '+ file_path)
                src_path = profiling_folder + '/' + file_path
                update_mongo(src_path)
                shutil.move(src_path, profiling_folder_processed + file_path)
                recv_file_count += 1
            except:
                print("Some Exception")

        print("Number of execution profiling files : " + str(recv_file_count))
        time.sleep(60)



if __name__ == '__main__':
    main()