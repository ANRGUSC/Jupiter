"""
.. note:: This is the main script to run in every node in the system for network profiling procedure.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import random
import subprocess
import pyinotify
from apscheduler.schedulers.background import BackgroundScheduler
import os
import csv
import paramiko
from scp import SCPClient
from pymongo import MongoClient
import datetime
import pandas as pd
import numpy as np
import time
import sys
from os import listdir
from os.path import isfile, join
from os import path

import configparser




def does_file_exist_in_dir(path):
    """Check if file exist in directory
    
    Args:
        path (str): directory path
    
    Returns:
        bool: ``True`` if exist, ``False`` otherwise
    """

    return any(isfile(join(path, i)) for i in listdir(path))


class droplet_measurement():
    """
    This class deals with the network profiling measurements.
    """
    def __init__(self):
        self.username   = username
        self.password   = password
        self.file_size  = [1,10,100,1000,10000]
        self.dir_local  = dir_local
        self.dir_remote = dir_remote
        self.my_host    = None
        self.my_region  = None
        self.hosts      = []
        self.regions    = []
        self.scheduling_file    = dir_scheduler
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
        self.parameters_file = 'parameters_%s'%(sys.argv[1])
        self.dir_remote      = dir_remote_central
        self.scheduling_file = dir_scheduler
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
                # print('**************************')
                # print(self.my_host)
                for row in reader:
                    self.hosts.append(row[0])
                    self.regions.append(row[1])
            # print('**************************')
            # print(self.hosts)
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

    def do_send_parameters(self):
        """This function sends the local regression data to the central profiler
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.central_IP, username = self.username,
                            password = self.password, port = ssh_port)
        local_path  = os.path.join(os.getcwd(),self.parameters_file)
        remote_path = '%s'%(self.dir_remote)
        scp = SCPClient(client.get_transport())
        scp.put(local_path, remote_path)
        scp.close()


class MyEventHandler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """

    def __init__(self):
        self.Mjob = None
        self.Rjob = None
        self.cur_file = None

    def prepare_database(self,filename):
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

    def regression_job(self):
        """Scheduling regression process every 10 minutes
        """
        print('Log regression every 10 minutes ....')
        d = droplet_regression()
        d.do_add_host(d.scheduling_file)
        d.do_regression()
        d.do_send_parameters()

    def measurement_job(self):
        """Scheduling logging measurement process every minute
        """
        print('Log measurement every minute ....')
        d = droplet_measurement()
        d.do_add_host(d.scheduling_file)
        d.do_log_measurement()


    def process_IN_CLOSE_WRITE(self, event):
        """On every node, whenever there is scheduling information sent from the central network profiler:
            - Connect the database
            - Scheduling measurement procedure
            - Scheduling regression procedure
            - Start the schedulers
        
        Args:
            event (ProcessEvent): a new file is created
        """

        print("CREATE event:", event.pathname)
        print(event.pathname)
        if self.Mjob == None:
            print('Step 1: Prepare the database')
            self.prepare_database(event.pathname)
            sched = BackgroundScheduler()

            print('Step 2: Scheduling measurement job')
            sched.add_job(self.measurement_job,'interval',id='measurement', minutes=1, replace_existing=True)

            print('Step 3: Scheduling regression job')
            sched.add_job(self.regression_job,'interval', id='regression', minutes=15, replace_existing=True)

            print('Step 4: Start the schedulers')
            sched.start()

            while True:
                time.sleep(10)
            sched.shutdown()
        else:
             print('New scheduling file, setting up a new job')



def main():
    """Start watching process for ``scheduling`` folder.
    """

    ##
    ## Load all the confuguration
    ##
    INI_PATH = '/network_profiling/jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    retry       = 1
    dir_local   = "generated_test"
    dir_remote  = "networkprofiling/received_test"
    dir_remote_central = "/network_profiling/parameters"
    dir_scheduler      = "scheduling/scheduling.txt"


    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])
    FLASK_SVC    = int(config['PORT']['FLASK_SVC'])
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])

    # watch manager
    wm = pyinotify.WatchManager()
    wm.add_watch('scheduling', pyinotify.ALL_EVENTS, rec=True)
    print('starting the process\n')
    # event handler
    eh = MyEventHandler()
    # notifier
    notifier = pyinotify.Notifier(wm, eh)
    # if does_file_exist_in_dir(os.path.dirname(os.path.abspath(__file__)) + "scheduling/"):


    notifier.loop()

if __name__ == '__main__':
    main()



