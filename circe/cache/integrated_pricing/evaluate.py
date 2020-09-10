#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script is used entirely for evaluation purpose.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"


import shutil
import os
import random
import time
import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import PatternMatchingEventHandler
import math
import configparser
import urllib
import urllib.request


def evaluate_random():
    """
    Copy files from folder ``sample_input`` to folder ``input`` at random intervals for evaluation 
    
    """
    file_count = len(os.listdir("sample_input/")) 
    interval = 120
    for i in range(1,file_count+1):
        n = random.randint(1,interval)
        count = 0
        while count<n:
            count = count+1
            time.sleep(1)
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)

def evaluate_interval(interval):
    """
    Copy files from folder ``sample_input`` to folder ``input`` at regular intervals for evaluation 

    Args:
        interval (int): interval time to inject the sample input file
    
    """
    file_count = len(os.listdir("sample_input/")) 
    for i in range(1,file_count+1):
        count = 0
        while count<interval:
            count = count+1
            time.sleep(1)
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)

def evaluate_sequential():
    """
    Copy files from folder ``sample_input`` to folder ``input`` one after another for evaluation 
    
    """
    file_count = len(os.listdir("sample_input/"))
    file_count_out = len(os.listdir("output/"))
    print('---- Generate random input files')
    for i in range(1,file_count+1):
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)
        count = 0
        while 1:
            time.sleep(5)
            file_count_out = len(os.listdir("output/"))
            if file_count_out ==  i:
                time.sleep(30)
                break


    print('---- Finish generating sequential input files')


def evaluate_stress(num_nodes):

    file_count = len(os.listdir("sample_input/"))
    file_count_out = len(os.listdir("output/"))
    num_stress = math.floor(file_count/3)
    requested = False
    print('---- Generate random input files')
    for i in range(1,file_count+1):
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        shutil.copyfile(src,dest)
        count = 0
        while 1:
            time.sleep(5)
            file_count_out = len(os.listdir("output/"))
            if file_count_out == num_stress and requested==False:
                print('Start to run stress test')
                request_stress_test(num_nodes)
                requested = True

            if file_count_out ==  i:
                time.sleep(30)
                break

def request_stress_test(num_nodes):
    node_ips = os.environ['ALL_SIM_IPS'].split(':')
    nodes = os.environ['ALL_SIM'].split(':')
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
    for i in range(0,num_nodes):
        print('---------- Request stress on the following node: '+nodes[i])
        worker_node_host_port =  node_ips[i]+ ":" + str(FLASK_SVC)
        try:
            url = "http://" + worker_node_host_port + "/start_stress_test"
            params = {'msg': 'request stress test'}
            params = urllib.parse.urlencode(params)
            req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
            res = urllib.request.urlopen(req)
            res = res.read()
            res = res.decode('utf-8')
        except Exception as e:
            print("Sending message to flask server on workers FAILED!!!")
            print(e)
            
    
class MyHandler(PatternMatchingEventHandler):
    """
    Handling the event when there is a new file generated in ``OUTPUT`` folder
    """

    def process(self, event):
        """
        Log the time the file is created and calculate the execution time whenever there is an event.
        
        Args:
            event: event to be watched for the ``OUTPUT`` folder
        """

        global start_times
        global end_times
        global exec_times
        global count

        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        if event.event_type == 'created':
            print("Received file as output in evaluation - %s." % event.src_path)  
            filename = os.path.split(event.src_path)[-1]
            appname = filename.split('-')[0]
            curfile = filename.split('-')[1].split('botnet')[0]
            curnum = int(curfile)+1
            if curnum < num_samples: 
                newfile = 'sample_input/'+appname+'-'+str(curnum)+'botnet.ipsum'
                fileout ='input/'+appname+'-'+str(curnum)+'botnet.ipsum'
                shutil.copyfile(newfile,fileout)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)
    

if __name__ == '__main__':
    my_id = os.environ['TASK']
    n = my_id.split('home')
    
    num = 1
    if n[1].isdigit():
        num = float(n[1])
    sleep_time_default = 240
    sleep_time = sleep_time_default + (num-1)*120
    print('The delay to send sample files')
    time.sleep(sleep_time)
    print('Start copying sample files for evaluation')
    evaluate_sequential()
    #evaluate_random()
    # time.sleep(300)
    # print('Start copying sample files for evaluation')
    # evaluate_sequential()