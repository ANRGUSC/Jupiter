"""
    .. note:: This is the main script to run in the central network profiler.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
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
import psutil
import paho.mqtt.client as mqtt
import _thread
from multiprocessing import Value, Process, Manager
import multiprocessing
import math

app = Flask(__name__)

def retrieve_resource():
    mem = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent()/ psutil.cpu_count()
    t = time.time()
    return mem,cpu,t

def schedule_monitor_resource(interval):
    """
    Schedulete the assignment update every interval
    
    Args:
        interval (int): chosen interval (minutes)
    
    """
    sched = BackgroundScheduler()
    sched.add_job(monitor_local_resources_EMA,'interval',id='assign_id', minutes=interval, replace_existing=True)
    sched.start()

def monitor_local_resources_EMA():
    """
    Obtain local resource stats (CPU, Memory usage and the lastest timestamp) from local node and store it to the variable ``local_resources``
    Using Exponential moving average
    """
    num_periods = 10
    
    print('Updating local resource stats (EMA)')
    cur_mem,cur_cpu,cur_time = retrieve_resource()
    if resource_profiling["count"] < (num_periods+1):
        resource_profiling["memory"] = (cur_mem + resource_profiling['memory'] * resource_profiling['count']) / (resource_profiling['count'] + 1)
        resource_profiling["cpu"] = (cur_cpu + resource_profiling['cpu'] * resource_profiling['count']) / (resource_profiling['count'] + 1)
    else:
        resource_profiling["memory"] = (cur_mem - resource_profiling["memory"])*(2/(num_periods+1)) + resource_profiling["memory"]
        resource_profiling["cpu"] = (cur_cpu - resource_profiling["cpu"])*(2/(num_periods+1)) + resource_profiling["cpu"]
    resource_profiling['count'] += 1
    resource_profiling['last_update'] = datetime.datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')

    try:
        logging  = resource_db[self_ip]
        new_log  = {'memory' : resource_profiling['memory'],
                    'cpu'    : resource_profiling['cpu'],
                    'count'  : resource_profiling['count'],
                    'last_update': resource_profiling['last_update']
                    }
        resource_id   = logging.insert_one(new_log).inserted_id
    except Exception as e:
        print('Error logging resource profiling information')
        print(e)
        

def demo_help(server,port,topic,msg):
    try:
        print('Sending demo')
        username = 'anrgusc'
        password = 'anrgusc'
        client = mqtt.Client()
        client.username_pw_set(username,password)
        client.connect(server, port,300)
        client.publish(topic, msg,qos=1)
        client.disconnect()
    except Exception as e:
        print('Sending demo failed')
        print(e)

def schedule_bokeh_profiling(interval):
    """
    Schedulete the assignment update every interval
    
    Args:
        interval (int): chosen interval (minutes)
    
    """
    sched = BackgroundScheduler()
    sched.add_job(announce_profiling,'interval',id='assign_id', seconds=interval, replace_existing=True)
    sched.start()

def announce_profiling():
    cur_cpu = psutil.cpu_percent() / psutil.cpu_count()
    cur_mem = psutil.virtual_memory().percent #used
    cur_time = time.time()
    topic = 'poweroverhead_%s'%(SELF_NAME)
    msg = 'poweroverhead %s cpu %f memory %f timestamp %f \n' %(SELF_NAME,cur_cpu,cur_mem,cur_time)
    demo_help(BOKEH_SERVER,BOKEH_PORT,topic,msg)

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
    if path.isfile(scheduler_file):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        while retry < num_retries:
            try:
                client.connect(ip, username = username, password = password,
                        port = ssh_port)
                scp = SCPClient(client.get_transport())
                scp.put(scheduler_file, dir_remote)
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
    db = client_mongo.central_network_profiler
    parameters_folder = os.path.join(os.getcwd(),'parameters')
    logging = db['quadratic_parameters']
    try:
        for subdir, dirs, files in os.walk(parameters_folder):
            for file in files:
                if file.startswith("."): 
                    continue
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
        #self.file_size  = [1,10,100,1000,10000]
        self.dir_local  = dir_local
        self.dir_remote = dir_remote
        self.my_host    = None
        self.my_region  = None
        self.hosts      = []
        self.regions    = []
        self.scheduling_file    = dir_scheduler
        self.measurement_script = os.path.join(os.getcwd(),'droplet_scp_time_transfer')
        self.db = client_mongo.droplet_network_profiler
        
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
        global file_size, cur_idx, num_files
        for idx in range (0, len(self.hosts)):
            print('Probing random messages')
            #random_size = random.choice(self.file_size)
            random_size = file_size[cur_idx.value]
            local_path  = '%s/%s_test_%dK'%(self.dir_local,self.my_host,random_size)
            remote_path = '%s'%(self.dir_remote)  
            # Run the measurement bash script     
            bash_script = self.measurement_script + " " +self.username + "@" + self.hosts[idx]
            bash_script = bash_script + " " + str(random_size)

            proc = subprocess.Popen(bash_script, shell = True, stdout = subprocess.PIPE)
            tmp = proc.stdout.read().strip().decode("utf-8")
            results = tmp.split(" ")[1]

            mins = float(results.split("m")[0])      # Get the minute part of the elapsed time
            secs = float(results.split("m")[1][:-1]) # Get the second potion of the elapsed time
            elapsed = mins * 60 + secs
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
        cur_idx.value = (cur_idx.value + 1) % num_files

class droplet_regression():
    """This class is used for the regression of the collected data
    """
    def __init__(self):
        self.db           = None
        self.my_host      = None
        self.my_region    = None
        self.hosts        = []
        self.regions      = []
        self.parameters_file = 'parameters_%s'%(self_ip)
        self.dir_remote      = dir_remote_central
        self.scheduling_file = dir_scheduler
        self.db = client_mongo.droplet_network_profiler
        self.username = username
        self.password = password
        self.central_IPs = HOME_IP.split(':')
        self.central_IPs = self.central_IPs[1:]
       
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

    def do_send_parameters(self):
        """This function sends the local regression data to the central profiler
        """
        print('Send to central nodes')
        for central_IP in self.central_IPs:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(central_IP, username = self.username,
                                password = self.password, port = ssh_port)
            local_path  = os.path.join(os.getcwd(),self.parameters_file)
            remote_path = '%s'%(self.dir_remote)
            scp = SCPClient(client.get_transport())
            scp.put(local_path, remote_path)
            scp.close()


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

def prepare_database(filename):
    """Connect to MongoDB server, prepare the database ``droplet_network_profiler`` at every node
    
    Args:
        filename (str): info file having the node's name/IP address
    """

    client = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/')
    db = client['droplet_network_profiler']
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

    global MONGO_DOCKER, FLASK_SVC, FLASK_DOCKER, num_retries, username, password, ssh_port, HOME_IP, min_file, max_file

    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    min_file = int(math.log10(int(config['OTHER']['MIN_SIZE'])))
    max_file = int(math.log10(int(config['OTHER']['MAX_SIZE'])))

    global file_size,num_files,cur_idx
    file_size  = [10**x for x in range(min_file,max_file+1)]
    num_files  = len(file_size)
    cur_idx = multiprocessing.Value('i', random.randint(0, num_files - 1))
    retry       = 1
    dir_local   = "generated_test"
    dir_remote  = "networkprofiling/received_test"
    dir_remote_central = "/network_profiling/parameters"
    dir_scheduler      = "scheduling/scheduling.txt"

    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])
    FLASK_SVC    = int(config['PORT']['FLASK_SVC'])
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])

    HOME_IP = os.environ["HOME_IP"]

    global dir_remote, dir_local, dir_scheduler, dir_remote_central, self_ip, filename
    self_ip = os.environ['SELF_IP']
    dir_remote         = '/network_profiling/scheduling/'
    dir_local          = "generated_test"
    dir_remote_central = "/network_profiling/parameters"
    dir_scheduler      = "scheduling/%s/scheduling.txt"%(self_ip)
    
    
    
    nodes_file = 'central_input/nodes.txt'
    homes_list = dict()
    node_list = dict()
    with open(nodes_file, 'r') as f:
        first_line = f.readline()
        lines = f.readlines()
        for line in lines:
            info = line.rstrip().split(',')
            node_list[info[0]] = [info[1],info[2]]
            if info[0].startswith('home'):
                homes_list[info[0]] = [info[1],info[2]]
                
    
    df_homes = pd.DataFrame.from_dict(homes_list, orient='index')  
    df_nodes = pd.DataFrame.from_dict(node_list, orient='index')
    df_homes.index.name = 'Tag'  
    df_nodes.index.name = 'Tag'
    df_homes.columns = ['Node', 'Region']
    df_nodes.columns = ['Node', 'Region']
    
    # print(df_homes)
    # print(df_nodes)

    # load the list of links from the csv file
    links_info = 'central_input/link_list.txt'
    df_links   = pd.read_csv(links_info, header = 0)
    df_links.replace('(^\s+|\s+$)', '', regex = True, inplace = True)

    # check the folder for putting output files
    global scheduling_folder, output_file
    scheduling_folder = 'scheduling'
    output_file = 'scheduling.txt'
    if not os.path.exists(scheduling_folder):
        os.makedirs(scheduling_folder)

    global client_mongo
    client_mongo = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/')


    print('Step 1: Create the central database ')
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

        # prepare the output schedule. it has two clumns Node and Region (location)
        schedule_info = pd.DataFrame(columns = ['Node','Region'])

        # Append the self ip address and the self region
        schedule_info = schedule_info.append({'Node':node_list.get(cur_node)[0],
                                    'Region':row['Region']}, ignore_index = True)
        # append all destination address and their region
        schedule_info = schedule_info.append(outgoing_links_info[['Node','Region']], ignore_index = False)
        # write the schedule to the output csv file

        scheduler_file = os.path.join(cur_schedule, output_file)

        schedule_info.to_csv(scheduler_file, header = False, index = False)



    filename = "scheduling/%s/scheduling.txt"%(self_ip)
    print(filename)
    prepare_database(filename)
        
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


    global BOKEH_SERVER, BOKEH_PORT, BOKEH, BOKEH_INTERVAL, SELF_NAME
    BOKEH_SERVER = config['OTHER']['BOKEH_SERVER']
    BOKEH_PORT = int(config['OTHER']['BOKEH_PORT'])
    BOKEH = int(config['OTHER']['BOKEH'])
    BOKEH_INTERVAL = int(config['OTHER']['BOKEH_INTERVAL'])
    SELF_NAME = os.environ['SELF_NAME']

    print('Bokeh information')
    print(BOKEH_SERVER)
    print(BOKEH_PORT)
    print(BOKEH)
    print(BOKEH_INTERVAL)
    print(SELF_NAME)

    ## Resource profiling
    global manager,resource_profiling
    manager = Manager()
    resource_profiling = manager.dict()
    resource_profiling['count'] = 0
    resource_profiling['cpu'] = 0
    resource_profiling['memory'] = 0
    resource_profiling['last_update'] = None
    num_periods = 10
    interval = 1

    global resource_client, resource_db
    resource_client = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/')
    resource_db = resource_client['central_resource_profiler']
    resource_db.create_collection(self_ip, capped=True, size = 100000,max=1000)

    if BOKEH==3:
        print('Step 7: Start sending profiling information (CPU,mem) to the bokeh server')
        _thread.start_new_thread(schedule_bokeh_profiling,(BOKEH_INTERVAL,))

    _thread.start_new_thread(schedule_monitor_resource,(interval,))


    


    app.run(host='0.0.0.0', port=FLASK_DOCKER) #run this web application on 0.0.0.0 and default port is 5000

if __name__ == '__main__':
    main()
    

