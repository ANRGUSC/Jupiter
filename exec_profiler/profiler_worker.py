
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
import sys
import paramiko
import time
from scp import SCPClient
from socket import gethostbyname, gaierror
import json
import datetime
import configparser

##
## Load all the confuguration
##
configs  = json.load(open('/centralized_scheduler/config.json'))
dag_flag = configs['exec_profiler']
task_map = configs['taskname_map']
nodename = os.environ['NODE_NAME']

HERE     = path.abspath(path.dirname(__file__)) + "/"
INI_PATH = HERE + 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)


##
## @brief      Convert bytes to Kbit as required by HEFT
## @param      num   The number pof bytes
## @return     { file size in Kbits }
##
def convert_bytes(num):
    return num*0.008

##
## @brief      Return the file size in bytes
## @param      file_path  The file path
## @return     { file size in bytes }
##
def file_size(file_path):
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)


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


print('{0:<16s} {1:<15s} {2:<5s} \n'.format('task', 'time (sec)', 'output_data (Kbit)'))
## write results in a text file
myfile = open(os.path.join(os.path.dirname(__file__), 'profiler_'+nodename+'.txt'), "w")
myfile.write('task,time(sec),output_data (Kbit)\n')

print(task_order)

#execute each task and get the timing and data size
for task in task_order:
    print('----------------------')
    try :

        module = task_module.get(task)
        os.environ['TASK'] = task
        print(task)

        start_time = datetime.datetime.utcnow()
        filename = module.main()
        stop_time = datetime.datetime.utcnow()
        mytime = stop_time - start_time
        mytime = int(mytime.total_seconds())


        output_data = [file_size(fname) for fname in filename]
        sum_output_data = sum(output_data) #current: summation of all output files
        line=task+','+str(mytime)+ ','+ str(sum_output_data) + '\n'
        print(line)
        myfile.write(line)
        myfile.flush()

    except Exception as e:
        print(e)

myfile.close()

print('Finish printing out the execution information')
print('Starting to send the output file back to the master node')



#send output file back to the scheduler machine
master_IP   = os.environ['HOME_NODE']
username    = config['AUTH']['USERNAME']
password    = config['AUTH']['PASSWORD']
ssh_port    = int(config['PORT']['SSH'])
num_retries = 20
retry       = 0

local_profiler_path    = os.path.join(os.path.dirname(__file__), 'profiler_' + nodename + '.txt')
remote_path = "/centralized_scheduler/profiler_files/"

# cmd = "sshpass -p " + password + " scp -P " + str(ssh_port) + " -o StrictHostKeyChecking=no %s %s:%s" % (local_profiler_path,master_IP, remote_path)
# print("cmd:", cmd)
# os.system(cmd)

if path.isfile(local_profiler_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while retry < num_retries:
        try:
            client.connect(master_IP, username=username, password=password, port=ssh_port)
            scp = SCPClient(client.get_transport())
            scp.put(local_profiler_path, remote_path)
            scp.close()
            # os.remove(local_profiler_path)
            print('execution profiling data transfer complete\n')
            break
        except (paramiko.ssh_exception.NoValidConnectionsError, gaierror):
            print('SSH Connection refused, will retry in 2 seconds')
            time.sleep(2)
            retry += 1
else:
    print('No Runtime data file exists...')

