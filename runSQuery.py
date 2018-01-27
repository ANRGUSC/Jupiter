"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import os
import csv
import pymongo
from pymongo import MongoClient
import pandas as pd
import json
import sys
import numpy as np
from datetime import datetime


class central_query_runtime():
    def __init__(self):
        self.client_mongo = MongoClient('mongodb://localhost:27017/')
        self.db = self.client_mongo.central_task_runtime_profiler

    def query_task(self,task_name,file_name):
        #logging_input = self.db['central_input']
        #logging_output = self.db['central_output']
        logging_droplet = self.db['droplet_runtime']
        input_timestamp = list(logging_droplet.find({"Task Name": task_name,'File Name':file_name,"Type":"created_input"}).sort([('Time', pymongo.ASCENDING)]))
        execution_timestamp = list(logging_droplet.find({"Task Name": task_name,'File Name':file_name,"Type":"execution_time"}).sort([('Time', pymongo.ASCENDING)]))
        finished_timestamp = list(logging_droplet.find({"Task Name": task_name,'File Name':file_name,"Type":"finished_time"}).sort([('Time', pymongo.ASCENDING)]))
        FMT = '%Y-%m-%d %H:%M:%S.%f'
        num_file = int(len(input_timestamp)/3)
        try:
            if num_file == 1:#only_1_file
                input_info = datetime.strptime(input_timestamp[0].get("Time"),FMT)
                execution_info = datetime.strptime(execution_timestamp[0].get("Time"),FMT)
                finished_info = datetime.strptime(finished_timestamp[0].get("Time"),FMT)
            else: #example: task 4 has 2 inputs from task 2, task 3
                input_info = datetime.strptime(input_timestamp[0].get("Time"),FMT)
                execution_info = datetime.strptime(execution_timestamp[0].get("Time"),FMT)
                finished_info = datetime.strptime(finished_timestamp[-1].get("Time"),FMT)

            duration_time = finished_info - execution_info
            waiting_time = execution_info - input_info
            # output_size = [str(x.get("File Size")) for x in finished_timestamp]
            # output_size = ",".join(output_size)
            output_size = [x.get("File Size") for x in finished_timestamp]
            output_size = sum(output_size)
            node_IP = input_timestamp[-1].get("Node IP")
            return node_IP,str(duration_time.total_seconds()), str(waiting_time.total_seconds()), str(output_size)
        except StopIteration:
            print('No valid Task/File')
            return -1


    def query_check_runtime(self,task_name,file_name):
        node_IP,duration_time, waiting_time, output_size = self.query_task(task_name,file_name)
        print('The task is performed at node '+ node_IP)
        print('The duration time is '+str(duration_time)+ " [sec] ; the waiting time is "+ str(waiting_time)+ " [sec]")
        print('The output size is ' + str(output_size)+ ' [Kbits]')

    def query_write_profile(self,file_name):
        print('Export runtime information to runtime_profile.txt as input file for the scheduler')
        logging_droplet = self.db['droplet_runtime']
        task_list = logging_droplet.find().distinct("Task Name")

        output_file='runtime_profile_%s.txt'%(file_name)
        f = open(output_file, 'w')
        f.write('task\ttime\toutput_data\n')
        for task in task_list:
            node_IP,duration_time, waiting_time, output_size = self.query_task(task,file_name)
            line = task+ '\t'+str(duration_time)+'\t'+ str(output_size)+'\n'
            f.write(line)
        f.close()


if __name__ == '__main__':
    d = central_query_runtime()
    if len(sys.argv)<2 or len(sys.argv)>3:
        print('Option 1 - Specific task & input file: python3 runSQuery [task_name] [input_task]')
        print('Option 2 - Write runtime profiler for a specific file: python3 runSQuery [input_task]')
        exit()
    if len(sys.argv)==2:
        file_name = sys.argv[1]
        d.query_write_profile(file_name)
    else:
        task_name = sys.argv[1]
        file_name = sys.argv[2]
        d.query_check_runtime(task_name,file_name)


