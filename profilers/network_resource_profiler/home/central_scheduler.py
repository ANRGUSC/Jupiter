"""
    .. note:: This is the main script to run in the central network profiler.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import pandas as pd
import os
import sys
from pymongo import MongoClient
import pandas as pd
import json
from apscheduler.schedulers.background import BackgroundScheduler
import time
import subprocess
import paramiko
from scp import SCPClient
import sys
from os import path
from socket import gethostbyname, gaierror
import configparser
from flask import Flask, Response, request, jsonify
import csv
import random
import datetime
import numpy as np

app = Flask(__name__)

def send_schedule(ip):
    """
    Sends the schedule to the requesting worker profiler

    Args:
        - ip (str): the ip address of the requesting worker

    Returns:
        dict: Status of the Schdule transfer ("Sucess" or "Fail")

    """
    cur_schedule = os.path.join(scheduling_folder, ip)
    scheduler_file = os.path.join(cur_schedule, output_file)
    retry = 1
    success_flag = False
    if path.isfile(scheduler_file) and path.isfile(source_central_file):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        while retry < num_retries:
            try:
                client.connect(ip, username = username, password = password,
                        port = ssh_port)
                scp = SCPClient(client.get_transport())
                scp.put(scheduler_file, dir_remote)
                scp.put(source_central_file, dir_remote_profiler)
                scp.close() 
                print('File transfer complete to ' + ip + '\n')
                success_flag = True
                break
            except (paramiko.ssh_exception.NoValidConnectionsError, gaierror):
                print('SSH Connection refused, will retry in 2 seconds')
                time.sleep(2)
                retry += 1
    else:
        print('No such file exists...')

    return_obj = {}
    if success_flag:
        return_obj['status'] = "Success"
    else:
        return_obj['status'] = "Fail"

    
    return json.dumps(return_obj)
app.add_url_rule('/schedule/<ip>', 'send_schedule', send_schedule)


def do_update_quadratic():
    """
    This function updates the estimated quadratic parameters in the mongodb server, database ``central_network_profiler``, collection ``quadratic_parameters``. It checks for any received files 
    from each of the worker droplets in the ``parameters/`` folder. If any a file exists, it updates the mongodb.
    """
    print('Update quadratic parameters from other nodes')
    client_mongo = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/') 
    db = client_mongo.central_network_profiler
    parameters_folder = os.path.join(os.getcwd(),'parameters')
    logging = db['quadratic_parameters']
    print(logging)
    try:
        for subdir, dirs, files in os.walk(parameters_folder):
            for file in files:
                if file.startswith("."): 
                    continue
                
                print(file)
                measurement_file = os.path.join(subdir, file)
                df = pd.read_csv(measurement_file, delimiter = ',', header = 0)
                data_json = json.loads(df.to_json(orient = 'records'))
                logging.insert(data_json)
    except Exception as e:
        print(e)

class droplet_measurement():
    """
    This class deals with the network profiling measurements.
    """
    def __init__(self):
        self.username   = username
        self.password   = password
        self.file_size  = [1,10,100,1000,10000]
        self.dir_local  = "generated_test"
        self.dir_remote = "networkprofiling/received_test"
        self.my_host    = None
        self.my_region  = None
        self.hosts      = []
        self.regions    = []
        self.scheduling_file    = "scheduling/%s/scheduling.txt"%(self_ip)
        self.measurement_script = os.path.join(os.getcwd(),'droplet_scp_time_transfer')
        self.client_mongo = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/')
        self.db = self.client_mongo.droplet_network_profiler
        
    def do_add_host(self, file_hosts):
        """This function reads the ``scheduler.txt`` file to add other droplets info 
        
        Args:
            file_hosts (str): the path of ``scheduler.txt``
        """
        if file_hosts:
            with open(file_hosts, 'r') as f:
                reader = csv.reader(f, delimiter=',')
                header = next(reader, None)
                self.my_host   = header[0]
                self.my_region = header[1]
                for row in reader:
                    self.hosts.append(row[0])
                    self.regions.append(row[1])
        else:
            print("No detected droplets information... ")

    def do_log_measurement(self):
        """This function pick a random file size, send the file to all of the neighbors and log the transfer time in the local Mongo database.
        """

        for idx in range (0, len(self.hosts)):
            random_size = random.choice(self.file_size)
            local_path  = '%s/%s_test_%dK'%(self.dir_local,self.my_host,random_size)
            remote_path = '%s'%(self.dir_remote)  
            # print(random_size)
            # Run the measurement bash script     
            bash_script = self.measurement_script + " " +self.username + "@" + self.hosts[idx]
            bash_script = bash_script + " " + str(random_size)

            print(bash_script)
            proc = subprocess.Popen(bash_script, shell = True, stdout = subprocess.PIPE)
            tmp = proc.stdout.read().strip().decode("utf-8")
            results = tmp.split(" ")[1]
            print(results)

            mins = float(results.split("m")[0])      # Get the minute part of the elapsed time
            secs = float(results.split("m")[1][:-1]) # Get the second potion of the elapsed time
            elapsed = mins * 60 + secs
            # print(elapsed)
            
            # Log the information in local mongodb
            cur_time = datetime.datetime.utcnow()
            logging  = self.db[self.hosts[idx]]
            new_log  = {"Source[IP]"        : self.my_host,
                        "Source[Reg]"       : self.my_region,
                        "Destination[IP]"   : self.hosts[idx],
                        "Destination[Reg]"  : self.regions[idx],
                        "Time_Stamp[UTC]"   : cur_time,
                        "File_Size[KB]"     : random_size,
                        "Transfer_Time[s]"  : elapsed}
            log_id   = logging.insert_one(new_log).inserted_id
            # print(log_id)


class droplet_regression():
    """This class is used for the regression of the collected data
    """
    def __init__(self):
        self.client_mongo = None
        self.db           = None
        self.my_host      = None
        self.my_region    = None
        self.hosts        = []
        self.regions      = []
        self.parameters_file = 'parameters_%s'%(self_ip)
        self.scheduling_file = "scheduling/%s/scheduling.txt"%(self_ip)
        self.client_mongo    = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/')
        self.db = self.client_mongo.droplet_network_profiler
       
        # Read the info regarding the central profiler
        with open('central.txt','r') as f:
            line = f.read().split(' ')
            self.central_IP = line[0]
            self.username   = line[1]
            self.password   = line[2]

    def do_add_host(self, file_hosts):
        """This function reads the ``scheduler.txt`` file to add other droplets info 
        
        Args:
            file_hosts (str): the path of ``scheduler.txt``
        """
        if file_hosts:
            with open(file_hosts, 'r') as f:
                reader = csv.reader(f, delimiter=',')
                header = next(reader, None)
                self.my_host   = header[0]
                self.my_region = header[1]
                for row in reader:
                    self.hosts.append(row[0])
                    self.regions.append(row[1])
        else:
            print("No detected droplets information... ")

    def do_regression(self):
        """This function performs the regression on the collected data, store the quaratic parameters in the local database, and write parameters into text file.
        """
        print('Store regression parameters in MongoDB')
        regression = self.db[self.my_host]
        reg_cols   = ['Source[IP]',
                      'Source[Reg]',
                      'Destination[IP]',
                      'Destination[Reg]',
                      'Time_Stamp[UTC]',
                      'Parameters']
        reg_data   = []
        reg_data.append(reg_cols)

        for idx in range(0,len(self.hosts)):
            host    = self.hosts[idx]
            logging = self.db[host]
            cursor  = logging.find({})
            df      = pd.DataFrame(list(cursor))

            df['X'] = df['File_Size[KB]'] * 8 #Kbits
            df['Y'] = df['Transfer_Time[s]'] * 1000 #ms

            # Quadratic prediction
            quadratic  = np.polyfit(df['X'],df['Y'],2)
            parameters = " ".join(str(x) for x in quadratic)
            cur_time   = datetime.datetime.utcnow()
            print(parameters)
            
            new_reg = { "Source[IP]"       : self.my_host,
                        "Source[Reg]"      : self.my_region,
                        "Destination[IP]"  : self.hosts[idx],
                        "Destination[Reg]" : self.regions[idx],
                        "Time_Stamp[UTC]"  : cur_time,
                        "Parameters"       : parameters}
            reg_id    = regression.insert_one(new_reg).inserted_id
            reg_entry = [ self.my_host,
                          self.my_region,
                          self.hosts[idx],
                          self.regions[idx],
                          str(cur_time),
                          parameters ]

            reg_data.append(reg_entry)

        # Write parameters into text file
        with open(self.parameters_file, "w") as f:
            print('Writing into file........')
            writer = csv.writer(f)
            writer.writerows(reg_data)


def regression_job():
    """Scheduling regression process every 10 minutes
    """
    print('Log regression every 10 minutes ....')
    d = droplet_regression()
    d.do_add_host(d.scheduling_file)
    d.do_regression()
    

def measurement_job():
    """Scheduling logging measurement process every minute
    """
    print('Log measurement every minute ....')
    d = droplet_measurement()
    d.do_add_host(d.scheduling_file)
    d.do_log_measurement()

def main():
    """
        - Load node information from ``central_input/nodes.txt`` and link list information from ``central_input/link_list.txt``
        - Create ``scheduling`` folder if not existed
        - Write central profiler info where each node should send their data
        - Create the central database
        - Preparing the scheduling files (neighbors info for each node including IP, username, password)
        - Copy files and network scripts to every droplets
        - Transfer the ``scheduler.txt`` and ``central.txt`` file to proper folders in order to trigger the profiling
        - Schedule updating the central database every minute
    """

    HERE     = path.abspath(path.dirname(__file__)) + "/"
    INI_PATH = HERE + 'jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global MONGO_DOCKER, FLASK_SVC, FLASK_DOCKER, num_retries, username, password, ssh_port

    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    retry       = 1


    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])
    FLASK_SVC    = int(config['PORT']['FLASK_SVC'])
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])

    global source_central_file, dir_remote, dir_remote_profiler,self_ip, filename
    dir_remote   = '/network_profiling/scheduling/'
    dir_remote_profiler  =  '/network_profiling/'
    source_central_file  = '/network_profiling/central.txt'
    self_ip = os.environ['SELF_IP']

    nodes_info = 'central_input/nodes.txt'
    df_nodes   = pd.read_csv(nodes_info, header = 0, delimiter = ',',index_col = 0)
    node_list  = df_nodes.T.to_dict('list')

    print(df_nodes)
    print(node_list)

    # load the list of links from the csv file
    links_info = 'central_input/link_list.txt'
    df_links   = pd.read_csv(links_info, header = 0)
    df_links.replace('(^\s+|\s+$)', '', regex = True, inplace = True)

    print(df_links)

    # check the folder for putting output files
    global scheduling_folder, output_file
    scheduling_folder = 'scheduling'
    output_file = 'scheduling.txt'
    if not os.path.exists(scheduling_folder):
        os.makedirs(scheduling_folder)

    # write central profiler info where each node should send their data
    with open(source_central_file, 'w') as f:
        line = self_ip+ " " + username + " " + password
        f.write(line)
    
    print('Step 1: Create the central database ')
    client_mongo = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/')
    db = client_mongo['central_network_profiler']
    buffer_size = len(df_links.index) * 100
    db.create_collection('quadratic_parameters', capped = True, size = 100000, max = buffer_size)
    

    print('Step 2: Preparing the scheduling text files')
    for cur_node, row in df_nodes.iterrows():
        # create separate scheduling folders for separate nodes
        cur_schedule = os.path.join(scheduling_folder, node_list.get(cur_node)[0])
        if not os.path.exists(cur_schedule):
            os.makedirs(cur_schedule)

        outgoing_links_info = df_links.loc[df_links['Source'] == cur_node]
        outgoing_links_info = pd.merge(outgoing_links_info, df_nodes, left_on = 'Destination', right_index = True, how = 'inner')

        print(outgoing_links_info)
        # prepare the output schedule. it has two clumns Node and Region (location)
        schedule_info = pd.DataFrame(columns = ['Node','Region'])
        # Append the self ip address and the self region
        schedule_info = schedule_info.append({'Node':node_list.get(cur_node)[0],
                                    'Region':row['Region']}, ignore_index = True)
        print(schedule_info)
        # append all destination address and their region
        schedule_info = schedule_info.append(outgoing_links_info[['Node','Region']], ignore_index = False)
        # write the schedule to the output csv file

        print(schedule_info)

        scheduler_file = os.path.join(cur_schedule, output_file)
        schedule_info.to_csv(scheduler_file, header = False, index = False)

    client_mongo = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/')
    db = client_mongo['droplet_network_profiler']
    filename = "scheduling/%s/scheduling.txt"%(self_ip)
    c = 0
    with open(filename, 'r') as f:
        next(f)
        for line in f:
            c =c+1
            ip, region = line.split(',')
            db.create_collection(ip, capped=True, size=10000, max=10)
    with open(filename, 'r') as f:
        first_line = f.readline()
        ip, region = first_line.split(',')
        db.create_collection(ip, capped=True, size=100000, max=c*100)
        
    print('Step 3: Scheduling updating the central database')
    # create the folder for each droplet/node to report the local data to
    parameters_folder = 'parameters'
    if not os.path.exists(parameters_folder):
        os.makedirs(parameters_folder)

    # create a background job to update the mongodb with the received parameters
    sched = BackgroundScheduler()
    sched.add_job(do_update_quadratic,'interval', id = 'update',
                               minutes = 10,replace_existing = True)
    

    print('Step 4: Scheduling measurement job')
    sched.add_job(measurement_job,'interval',id='measurement', minutes=1, replace_existing=True)

    print('Step 5: Scheduling regression job')
    sched.add_job(regression_job,'interval', id='regression', minutes=10, replace_existing=True)

    print('Step 6: Start the schedulers')
    sched.start()

    app.run(host='0.0.0.0', port=FLASK_DOCKER) #run this web application on 0.0.0.0 and default port is 5000

if __name__ == '__main__':
    main()
    

