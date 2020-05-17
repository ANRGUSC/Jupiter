__author__ = "Pradipta Ghosh, Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

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
import paho.mqtt.client as mqtt

def demo_help(server,port,topic,msg):
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()

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
            for line in f:
                parts = line.split()
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
        for line in f:
            parts = line.split()
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

def transfer_data_scp(ID,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        ID (str): destination ID
        user (str): username
        pword (str): password
        source (str): source file path
        destination (str): destination file path
    """

    #Keep retrying in case the containers are still building/booting up on
    #the child nodes.
    retry = 0
    while retry < num_retries:
        try:
            nodeIP = combined_ip_map[ID]
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user,nodeIP, destination)
            os.system(cmd)
            print('data transfer complete\n')
            break
        except:
            print('profiler_home.txt: SSH Connection refused or File transfer failed, will retry in 2 seconds')
            time.sleep(2)
            retry += 1


def transfer_data(ID,user,pword,source, destination):
    """Transfer data with given parameters
    
    Args:
        ID (str): destination ID 
        user (str): destination username
        pword (str): destination password
        source (str): source file path
        destination (str): destination file path
    """
    msg = 'Transfer to ID: %s , username: %s , password: %s, source path: %s , destination path: %s'%(ID,user,pword,source, destination)
    print(msg)
    
    if TRANSFER == 0:
        return transfer_data_scp(ID,user,pword,source, destination)

    return transfer_data_scp(ID,user,pword,source, destination) #default

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
    print('Starting to run execution profiler')
    starting_time = time.time()

    HERE     = path.abspath(path.dirname(__file__)) + "/"
    INI_PATH = HERE + 'jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global MONGO_PORT,EXC_FPORT

    EXC_FPORT = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT = int(config['PORT']['MONGO_DOCKER'])

    configs = json.load(open('/centralized_scheduler/config.json'))
    dag_flag = configs['exec_profiler']
    task_map = configs['taskname_map']

    global TRANSFER
    TRANSFER = int(config['CONFIG']['TRANSFER'])

    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])


    nodename = 'home'
    print(nodename)

    client_mongo = MongoClient('mongodb://localhost:'+ str(MONGO_PORT) +'/')
    db = client_mongo['execution_profiler']

    num_profiling_files = 0
    profiling_folder = '/centralized_scheduler/profiler_files'
    profiling_folder_processed = '/centralized_scheduler/profiler_files_processed/'



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

    ## import task modules, put then in a list and create task-module dictinary
    task_module = {}
    modules=[]
    for task in tasks.keys():
        os.environ['TASK'] = task
        taskmodule  = __import__(task)
        modules.append(taskmodule)
        task_module[task]=(taskmodule)


    ## execute each task and get the timing and data size
    myfile = open(os.path.join(os.path.dirname(__file__), 'profiler_'+nodename+'.txt'), "w")
    myfile.write('task,time(sec),output_data (Kbit)\n')

    count = 0
    for task in task_order:

        module = task_module.get(task)
        os.environ['TASK'] = task
        count = count+1

        start_time = datetime.datetime.utcnow()
        filename = module.main()
        print('------------------------------------------------')
        print(filename)
        stop_time = datetime.datetime.utcnow()
        mytime = stop_time - start_time
        mytime = mytime.total_seconds()

        output_data = [file_size(fname) for fname in filename]
        print(output_data)
        print('------------------------------------------------')
        sum_output_data = sum(output_data) #current: summation of all output files
        line=task+','+str(mytime)+ ','+ str(sum_output_data) + '\n'
        myfile.write(line)
        myfile.flush()



    myfile.close()

    print('Finish printing out the execution information')

    ## data sources
    datasources = []
    num_files = 0
    with open(os.path.join(os.path.dirname(__file__), 'nodes.txt'), "r") as nFile:
        for line in nFile:
            node_line = line.strip().split(" ")
            num_files = num_files+1
            if node_line[0].startswith('datasource'):
                datasources.append(node_line[0])


    print(datasources)
    for ds in datasources:
        src_path = os.path.join(os.path.dirname(__file__), 'profiler_'+ds+'.txt')
        myfile = open(src_path, "w")
        myfile.write('task,time(sec),output_data (Kbit)\n')

        ## write results in a text file
        

        BIG_NUM = '100000000000000'
        for task in task_order:
            mytime = int(BIG_NUM) 
            sum_output_data = int(BIG_NUM) 
            line=task+','+str(mytime)+ ','+ str(sum_output_data) + '\n'
            myfile.write(line)
            myfile.flush()
        myfile.close()

        update_mongo(src_path)
        processed_file = os.path.join(profiling_folder_processed,'profiler_'+ds+'.txt')
        shutil.move(src_path,  processed_file)

    print('Starting to send the output file back to the master node')


    # TODO: send the intermedaiate files to the remote location
    # TODO: send a signal to the k8 to remove the nonDAG tasks

    ## send intermediate files to the worker execution profilers
    global username,password,ssh_port,num_retries

    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])

    print('Copy supertask information to profilers folder')
    master_profile_file_name = os.path.join(os.path.dirname(__file__), 'profiler_' + nodename + '.txt')
    local_profiler_path    = os.path.join(os.path.dirname(__file__), 'profiler_files/')
    if path.isfile(master_profile_file_name):
        os.system('mv ' + master_profile_file_name + ' ' + local_profiler_path)

    nonDAG_file = local_profiler_path+ 'profiler_home.txt'
    print('update non DAG info in MongoDB')
    client_mongo = MongoClient('mongodb://localhost:'+ str(MONGO_PORT) +'/')
    db = client_mongo['execution_profiler']

    profilers_ips = os.environ['ALL_PROFILERS_IPS'].split(':')
    allprofiler_names = os.environ['ALL_PROFILERS_NAMES'].split(':')
    ptFile = "/centralized_scheduler/generated_files/"
    ptFile1 = "/centralized_scheduler/"
    profilers_ips = profilers_ips[1:]
    allprofiler_names= allprofiler_names[1:]

    global ip_profilers_map, profilers_ip_map
    ip_profilers_map = dict(zip(profilers_ips, allprofiler_names))
    profilers_ip_map = dict(zip(allprofiler_names, profilers_ips))
 
    global combined_ip_map
    combined_ip_map = dict(zip(allprofiler_names, profilers_ips))
    """
        Transfer the Intermdiate Files Tt all the Workers. 
    """
    for node in allprofiler_names:
        print('----------------------------------')
        print("Sending data to execution worker of ", node)
        transfer_data(node,username,password,ptFile, ptFile1)
        try:
            print("start the profiler in ", node)
            print(profilers_ip_map[node])
            r = requests.get("http://"+profilers_ip_map[node]+":" + str(EXC_FPORT))
            result = r.json()
        except Exception as e:
            print("Exception in sending data")
            print(e)


    if BOKEH==3:
        msg = 'msgoverhead executionprofiler sendsample %d\n'%(len(profilers_ips))
        demo_help(BOKEH_SERVER,BOKEH_PORT,"msgoverhead_home",msg)
        msg = 'msgoverhead executionprofiler startprofiler %d\n'%(len(profilers_ips))
        demo_help(BOKEH_SERVER,BOKEH_PORT,"msgoverhead_home",msg)




    ## Start Waiting For Incoming Statistics from the Worker Execution Profilers
    ## Once a File arrives at the profiling_folder immediately process it and
    ## move it to the profiling_folder_processed to keep track of processed files

    print('Watching the incoming execution profiler files')
    
    ## Copy profiler files for data sources:


    recv_file_count = 0
    while recv_file_count<num_files:

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
        if recv_file_count == num_files:
            print('Successfully finish execution profiler ')
            end_time = time.time()
            deploy_time = end_time - starting_time
            print('Time to finish execution profiler '+ str(deploy_time))
            break
        time.sleep(60)

    

    while 1:
        print("Finish execution profiling : " + str(recv_file_count))
        time.sleep(60)

if __name__ == '__main__':
    main()
