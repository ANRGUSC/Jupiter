__author__ = "Pradipta Ghosh, Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import timeit
import os
from os import path
import sys
import paramiko
import time
from scp import SCPClient
from socket import gethostbyname, gaierror
import json
import datetime
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

def transfer_data_scp(IP,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        IP (str): destination IP address
        user (str): username
        pword (str): password
        source (str): source file path
        destination (str): destination file path
    """
    #Keep retrying in case the containers are still building/booting up on
    #the child nodes.
    # print(IP)
    retry = 0
    while retry < num_retries:
        try:
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, IP, destination)
            os.system(cmd)
            print('data transfer complete\n')
            break
        except:
            print('profiler_worker.txt: SSH Connection refused or File transfer failed, will retry in 2 seconds')
            time.sleep(2)
            retry += 1


def transfer_data(IP,user,pword,source, destination):
    """Transfer data with given parameters
    
    Args:
        IP (str): destination IP 
        user (str): destination username
        pword (str): destination password
        source (str): source file path
        destination (str): destination file path
    """
    msg = 'Transfer to IP: %s , username: %s , password: %s, source path: %s , destination path: %s'%(IP,user,pword,source, destination)
    print(msg)
    
    if TRANSFER == 0:
        return transfer_data_scp(IP,user,pword,source, destination)

    return transfer_data_scp(IP,user,pword,source, destination) #default

def main():
    """
        -   Load all the confuguration
        -   create the task list in the order of execution
        -   execute each task and get the timing and data size
        -   send output file back to the scheduler machine
    """
    # Load all the confuguration
    
    # configs  = json.load(open('/centralized_scheduler/config.json'))
    # dag_flag = configs['exec_profiler']
    # task_map = configs['taskname_map']
    # nodename = os.environ['NODE_NAME']

    # HERE     = path.abspath(path.dirname(__file__)) + "/"
    # INI_PATH = HERE + 'jupiter_config.ini'
    # config = configparser.ConfigParser()
    # config.read(INI_PATH)

    print('Load all the configuration')
    configs  = json.load(open('/centralized_scheduler/config.json'))
    dag_flag = configs['exec_profiler']
    task_map = configs['taskname_map']
    nodename = os.environ['NODE_NAME']

    HERE     = path.abspath(path.dirname(__file__)) + "/"
    INI_PATH = HERE + 'jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)


    # print('-----')
    # print(configs)
    # print(dag_flag)
    # print(task_map)
    # print(nodename)
    # print(os.environ['ALL_NODES'])
    # print('-----')

    global TRANSFER
    TRANSFER = int(config['CONFIG']['TRANSFER'])
    # print(TRANSFER)

    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])

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
        if dag_flag[data[0]] == False or task_map[data[0]][1] == False:
            continue

        tasks.setdefault(data[0], [])
        if data[0] not in task_order:
            task_order.append(data[0])

        for i in range(3, len(data)):
            if data[i] != 'home' and dag_flag[data[i]] == True and task_map[data[i]][1] == True:
                tasks[data[0]].append(data[i])

    # print("tasks: ", tasks)

    ## import task modules, put then in a list and create task-module dictinary
    task_module = {}
    modules=[]
    for task in tasks.keys():
        # print(task)
        os.environ['TASK'] = task
        taskmodule  = __import__(task)
        modules.append(taskmodule)
        task_module[task]=(taskmodule)


    # print('{0:<16s} {1:<15s} {2:<5s} \n'.format('task', 'time (sec)', 'output_data (Kbit)'))
    ## write results in a text file
    myfile = open(os.path.join(os.path.dirname(__file__), 'profiler_'+nodename+'.txt'), "w")
    myfile.write('task,time(sec),output_data (Kbit)\n')

    # print(task_order)

    #execute each task and get the timing and data size
    count = 0
    for task in task_order:
        # print('----------------------')
        try :

            module = task_module.get(task)
            os.environ['TASK'] = task
            # print(task)
            print(count)
            count = count+1

            start_time = datetime.datetime.utcnow()
            filename = module.main()
            # print('------------------------------------------------')
            # print(filename)
            stop_time = datetime.datetime.utcnow()
            mytime = stop_time - start_time
            mytime = int(mytime.total_seconds())


            output_data = [file_size(fname) for fname in filename]
            # print(output_data)
            # print('------------------------------------------------')
            sum_output_data = sum(output_data) #current: summation of all output files
            line=task+','+str(mytime)+ ','+ str(sum_output_data) + '\n'
            # print(line)
            myfile.write(line)
            myfile.flush()

        except Exception as e:
            print(e)

    myfile.close()

    print('Finish printing out the execution information')
    print('Starting to send the output file back to the master node')



    #send output file back to the scheduler machine
    global username,password,ssh_port,num_retries

    master_IP   = os.environ['HOME_NODE']
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])


    local_profiler_path    = os.path.join(os.path.dirname(__file__), 'profiler_' + nodename + '.txt')
    remote_path = "/centralized_scheduler/profiler_files/"

    if path.isfile(local_profiler_path):
        transfer_data(master_IP,username,password,local_profiler_path, remote_path)
        if BOKEH==5:
            topic = "msgoverhead_%s"%(nodename)
            msg = 'msgoverhead executionprofiler sendexecinfo %d\n'%(len(tasks))
            demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)
    else:
        print('No Runtime data file exists...')

if __name__ == '__main__':
    main()

