#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script runs on the scheduler node of CIRCE. 

"""

__author__ = "Aleksandra Knezevic,Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,   Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import paramiko
from scp import SCPClient
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import json
from multiprocessing import Process, Manager
from readconfig import read_config
from socket import gethostbyname, gaierror, error

from watchdog.events import PatternMatchingEventHandler
import multiprocessing
from flask import Flask, request
from collections import defaultdict

from os import path
import configparser
import numpy as np
from collections import defaultdict
import paho.mqtt.client as mqtt
import jupiter_config
import logging
import pyinotify
from datetime import datetime




app = Flask(__name__)

def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def demo_help(server,port,topic,msg):
    logging.debug('Sending demo')
    logging.debug(topic)
    logging.debug(msg)
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username,password)
    client.connect(server, port,300)
    client.publish(topic, msg,qos=1)
    client.disconnect()

def recv_datasource():
    """

    Receiving run-time profiling information from WAVE/HEFT for every task (task name, start time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """
    global start_times, end_times
    try:
        # logging.debug('Receive final runtime profiling')
        filename = request.args.get('filename')
        filetype = request.args.get('filetype')
        ts = request.args.get('time')

        logging.debug("Received flask message: %s %s %s", filename, filetype,ts)
        logging.debug('The data source generates the input file: ')
        if filetype == 'input':
            start_times[filename]=float(ts)
            logging.debug(start_times)
        else:
            logging.debug('Something wrong with receiving monitor information from data sources')

        
    except Exception as e:
        logging.debug("Bad reception or failed processing in Flask receiving datasource")
        logging.debug(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_monitor_datasource', 'recv_datasource', recv_datasource)

def recv_datasink():
    """

    Receiving run-time profiling information from datasinks
    
    Raises:
        Exception: failed processing in Flask
    """
    global start_times, end_times
    try:
        # logging.debug('Receive final runtime profiling')
        filename = request.args.get('filename')
        filetype = request.args.get('filetype')
        ts = request.args.get('time')

        logging.debug("Received flask message: %s %s %s", filename, filetype,ts)
        if filetype == 'output':
            end_times[filename]=float(ts)
            logging.debug(start_times)
        else:
            logging.debug('Something wrong with receiving monitor information from data sinks')
    except Exception as e:
        logging.debug("Bad reception or failed processing in Flask receiving datasink")
        logging.debug(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_monitor_datasink', 'recv_datasink', recv_datasink)

# def recv_mapping():
#     """

#     Receiving run-time profiling information from WAVE/HEFT for every task (task name, start time stats, end time stats)
    
#     Raises:
#         Exception: failed processing in Flask
#     """

#     global start_time
#     global end_time

#     try:
#         worker_node = request.args.get('work_node')
#         msg = request.args.get('msg')
#         ts = datetime.utcnow()

#         logging.debug("Received monitor flask message:%s %s %s", worker_node, msg, ts)
#         if msg == 'start':
#             start_time[worker_node].append(unix_time(ts))
#         else:
#             end_time[worker_node].append(unix_time(ts))
#             # if worker_node in last_tasks:
#             #     logging.debug("Start time stats: %s", start_time)
#             #     logging.debug("End time stats: %s", end_time)


#     except Exception as e:
#         logging.debug("Bad reception or failed processing in Flask")
#         logging.debug(e)
#         return "not ok"
#     return "ok"
# app.add_url_rule('/recv_monitor_data', 'recv_mapping', recv_mapping)

def return_output_files():
    """
    Return number of output files
    
    Returns:
        int: number of output files
    """
    num_files = len(os.listdir("output/"))
    # logging.debug("Recieved request for number of output files. Current done:", num_files)
    return json.dumps(num_files)
app.add_url_rule('/', 'return_output_files', return_output_files)

# def recv_runtime_profile():
#     """

#     Receiving run-time profiling information for every task (task name, start time stats, waiting time stats, end time stats)
    
#     Raises:
#         Exception: failed processing in Flask
#     """

#     global rt_enter_time
#     global rt_exec_time
#     global rt_finish_time

#     try:
#         logging.debug('Receive runtime stats information: ')
#         worker_node = request.args.get('work_node')
#         msg = request.args.get('msg').split()
        
        
#         if msg[0] == 'rt_enter':
#             rt_enter_time[(worker_node,msg[1])] = float(msg[2])
#         elif msg[0] == 'rt_exec' :
#             rt_exec_time[(worker_node,msg[1])] = float(msg[2])
#         else: #rt_finish
#             rt_finish_time[(worker_node,msg[1])] = float(msg[2])
#             if worker_node in last_tasks:
#                 # Per task stats:
#                 logging.debug('********************************************') 
#                 logging.debug("Received final output at home: Runtime profiling info:")
#                 """
#                     - Worker node: task name
#                     - Input file: input files
#                     - Enter time: time the input file enter the queue
#                     - Execute time: time the input file is processed
#                     - Finish time: time the output file is generated
#                     - Elapse time: total time since the input file is created till the output file is created
#                     - Duration time: total execution time of the task
#                     - Waiting time: total time since the input file is created till it is processed
#                 """
#                 log_file = open(os.path.join(os.path.dirname(__file__), 'runtime_tasks.txt'), "w")
#                 s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Task_name','local_input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time')
#                 logging.debug(s)
#                 log_file.write(s)

#                 for k, v in rt_enter_time.items():
#                     logging.debug(k)
#                     logging.debug(rt_finish_time)
#                     logging.debug(msg[1])
#                     if k in rt_finish_time:
#                         print('-----')
#                         elapse = rt_finish_time[k]-v
#                         duration = rt_finish_time[k]-rt_exec_time[k]
#                         waiting = rt_exec_time[k]-v
#                         s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(worker, file, v, rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting))
#                         logging.debug(s)
#                         log_file.write(s)
#                         log_file.flush()

#                 log_file.close()
#                 logging.debug('********************************************')
        

                
#     except Exception as e:
#         logging.debug("Bad reception or failed processing in Flask for runtime profiling")
#         logging.debug(e)
#         return "not ok"
#     return "ok"
# app.add_url_rule('/recv_runtime_profile', 'recv_runtime_profile', recv_runtime_profile)

# def update_demo_stats():
#     global rt_enter_time
#     global rt_exec_time
#     global rt_finish_time
#     global rt_enter_task_time
#     global rt_finish_task_time 

#     logging.debug('********************************************') 
#     logging.debug("Update stats information")
#     logging.debug(outputfiles)
#     """
#         - Worker node: task name
#         - Input file: input files
#         - Enter time: time the input file enter the queue
#         - Execute time: time the input file is processed
#         - Finish time: time the output file is generated
#         - Elapse time: total time since the input file is created till the output file is created
#         - Duration time: total execution time of the task
#         - Waiting time: total time since the input file is created till it is processed
#     """
#     # logging.debug('Enter time')
#     # logging.debug(rt_enter_time)
#     # logging.debug('Exec time')
#     # logging.debug(rt_exec_time)
#     # logging.debug('Finish time')
#     # logging.debug(rt_finish_time)
#     log_file = open(os.path.join(os.path.dirname(__file__), 'runtime_tasks.txt'), "w")
#     s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Task_name','local_input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time','Real execution time', 'Prewaiting','Postwaiting')
#     log_file.write(s)
#     logging.debug(s)



#     # for k,v in rt_finish_time.items():
#     #     if k in rt_enter_time and k in rt_exec_time:
#     #         elapse = rt_finish_time[k]-rt_enter_time[k]  
#     #         duration = rt_finish_time[k]-rt_exec_time[k]
#     #         waiting = rt_exec_time[k] - rt_enter_time[k]
#     #         image_set.add(k[1])
#     #         s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(k[0], k[1], rt_enter_time[k], rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting))
#     #         statstime[k] = [rt_enter_time[k], rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting)]
#     #         #logging.debug(s)
#     #         log_file.write(s)
#     #         log_file.flush()
#     #     else:
#     #         logging.debug('Missing profiling file information...')

#     for k,v in rt_finish_time.items():
#         elaspe = 0
#         duration = 0
#         waiting = 0
#         duration_task = 0
#         pre_waiting = 0
#         post_waiting = 0
#         try:
#             elapse = rt_finish_time[k]-rt_enter_time[k]  
#         except:
#             rt_enter_time[k] = 0
#             logging.debug('no enter time')

#         try:
#             duration = rt_finish_time[k]-rt_exec_time[k]
#         except:
#             rt_exec_time[k] = 0
#             logging.debug('no exec time')
        
#         try:
#             waiting = rt_exec_time[k] - rt_enter_time[k]
#         except:
#             logging.debug('no enter/exec time')

#         try:
#             duration_task = rt_finish_task_time[k]-rt_enter_task_time[k]
#         except:
#             logging.debug('no finish/enter task time')

#         try:
#             pre_waiting = rt_enter_task_time[k] - rt_enter_time[k] 
#         except:
#             logging.debug('no enter/enter task time')

#         try:
#             post_waiting = rt_finish_time[k] - rt_finish_task_time[k]
#         except:
#             logging.debug('no finish/finish task time')

#         image_set.add(k[1])
#         # s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(k[0], k[1], rt_enter_time[k], rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting),str(duration_task),str(pre_waiting),str(post_waiting))
#         statstime[k] = [rt_enter_time[k], rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting),str(duration_task),str(pre_waiting),str(post_waiting)]


#     # log_file.close()
#     logging.debug('********************************************')
#     logging.debug('Intermediate tasks :')
#     logging.debug(statstime)
#     logging.debug('********************************************')
#     logging.debug("Communication time :")

#     for item in image_set:
#         timeseq = [(k[0],v) for k,v in statstime.items() if k[1]==item]
#         timedict = dict(timeseq)
#         # logging.debug(timedict)
#         try:
#             comm_time[(item,'datasource','master')] = timedict['master'][0] - start_times[item]
#         except Exception as e:
#             pass
#             # logging.debug('Missing datasource stats information')
#             # logging.debug(e)
#             # logging.debug(timedict['master'][0])
#             # logging.debug(start_times[item])
#         # logging.debug(comm_time)
#         for task in dag:
#             if task.startswith('lccdec'):
#                 try:
#                     # logging.debug('last task')
#                     comm_time[(item, task,'home')] = end_times[item] - timedict[task][2] 

#                 except Exception as e:
#                     pass
#                     # logging.debug('Missing lccdec stats information')
#                     # logging.debug(end_times.keys())
#                     # logging.debug(timedict.keys())
#                     # logging.debug(e)
#                     # logging.debug('Last task: only belong to one class')
#             else:
#                 for next_task in dag[task][2:]:
#                     try:
#                         comm_time[(item, task,next_task)] = timedict[next_task][0]-timedict[task][2]
#                     except Exception as e:
#                         pass
#                         # logging.debug('Only belong to one class / collage task')
#                         # logging.debug(e)
#                         # logging.debug(e)


#     logging.debug(comm_time)
#     logging.debug('********************************************') 


#demo application : not merger rt_finish & rt_finish_task
# def recv_runtime_profile_old():
#     """

#     Receiving run-time profiling information for every task (task name, start time stats, waiting time stats, end time stats)
    
#     Raises:
#         Exception: failed processing in Flask
#     """

#     global rt_enter_time
#     global rt_exec_time
#     global rt_finish_time
#     global rt_enter_task_time
#     global rt_finish_task_time 

#     try:
#         logging.debug('Receive runtime stats information: ')
#         worker_node = request.args.get('work_node')
#         msg = request.args.get('msg').split()

#         action = msg[0]
#         from_task = msg[1]
#         fname = msg[2]
#         ts = float(msg[3])

#         # logging.debug(msg)

#         classlists = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard',  'lion', 'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
#         classids = np.arange(0,len(classlists),1)
#         classids = [str(x) for x in classids]
#         classmap = dict(zip(classids,classlists))

#         if '-' in fname:
#             outputfile = fname.split('.')[0].split('-')
#             logging.debug(outputfile)
#             outputfiles = []
#             logging.debug(classmap)
#             for fi in outputfile:
#                 tmp = fi.split('#')[1]+'img'+ classmap[fi.split('#')[0]]+'.JPEG'
#                 outputfiles.append(tmp)
#         else:
#             outputfiles = [fname]

#         # logging.debug(outputfiles)
#         # logging.debug(from_task)
#         # logging.debug(action)

#         if action == 'rt_enter': # first file            
#             for i in range(0,len(outputfiles)):
#                 if (worker_node,from_task,outputfiles[i]) in rt_enter_time:
#                     logging.debug('Already exists enter...')
#                     logging.debug(rt_enter_time[(worker_node,from_task,outputfiles[i])])
#                     continue
#                 rt_enter_time[(worker_node,from_task,outputfiles[i])] = ts

#             # logging.debug(rt_enter_time)
                
#         elif action == 'rt_exec' : # first file            
#             for i in range(0,len(outputfiles)):
#                 if (worker_node,from_task,outputfiles[i]) in rt_exec_time:
#                     logging.debug('Already exists exec...')
#                     logging.debug(rt_exec_time[(worker_node,from_task,outputfiles[i])])
#                     continue
#                 rt_exec_time[(worker_node,from_task,outputfiles[i])] = ts
#             # logging.debug(rt_exec_time)
#         elif action == 'rt_enter_task' : # first file            
#             for i in range(0,len(outputfiles)):
#                 if (worker_node,from_task,outputfiles[i]) in rt_enter_task_time:
#                     logging.debug('Already exists enter task...')
#                     logging.debug(rt_enter_task_time[(worker_node,from_task,outputfiles[i])])
#                     continue
#                 rt_enter_task_time[(worker_node,from_task,outputfiles[i])] = ts
#         elif action == 'rt_finish_task' : #last file            
#             for i in range(0,len(outputfiles)): 
#                 rt_finish_task_time[(worker_node,from_task,outputfiles[i])] = ts                
#         elif action == 'rt_finish' :#last file            
#             for i in range(0,len(outputfiles)): 
#                 rt_finish_time[(worker_node,from_task,outputfiles[i])] = ts
            
#             if worker_node in last_tasks:
#                 # Per task stats:
#                 logging.debug('********************************************') 
#                 logging.debug("Received final output at home: Runtime profiling info:")
#                 # logging.debug(outputfiles)
#                 """
#                     - Worker node: task name
#                     - Input file: input files
#                     - Enter time: time the input file enter the queue
#                     - Execute time: time the input file is processed
#                     - Finish time: time the output file is generated
#                     - Elapse time: total time since the input file is created till the output file is created
#                     - Duration time: total execution time of the task
#                     - Waiting time: total time since the input file is created till it is processed
#                 """
#                 log_file = open(os.path.join(os.path.dirname(__file__), 'runtime_tasks.txt'), "w")
#                 s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Task_name','From_task','local_input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time','Real execution time', 'Prewaiting','Postwaiting')
#                 log_file.write(s)
#                 logging.debug(s)

#                 for k,v in rt_finish_time.items():
#                     elaspe = 0
#                     duration = 0
#                     waiting = 0
#                     duration_task = 0
#                     pre_waiting = 0
#                     post_waiting = 0
#                     try:
#                         elapse = rt_finish_time[k]-rt_enter_time[k]  
#                     except Exception as e:
#                         rt_enter_time[k] = 0
#                         logging.debug('no enter time')
#                         logging.debug(e)

#                     try:
#                         duration = rt_finish_time[k]-rt_exec_time[k]
#                     except Exception as e:
#                         rt_exec_time[k] = 0
#                         logging.debug('no exec time')
#                         logging.debug(e)
                    
#                     try:
#                         waiting = rt_exec_time[k] - rt_enter_time[k]
#                     except Exception as e:
#                         logging.debug('no enter/exec time')
#                         logging.debug(e)
                        
#                     try:
#                         duration_task = rt_finish_task_time[k]-rt_enter_task_time[k]
#                     except Exception as e:
#                         logging.debug('no finish/enter task time')
#                         logging.debug(e)

#                     try:
#                         pre_waiting = rt_enter_task_time[k] - rt_enter_time[k] 
#                     except Exception as e:
#                         logging.debug('no enter/enter task time')
#                         logging.debug(e)

#                     try:
#                         post_waiting = rt_finish_time[k] - rt_finish_task_time[k]#not yet know why
#                         if post_waiting<0: 
#                             post_waiting = 0
#                     except Exception as e:
#                         logging.debug('no finish/finish task time')
#                         logging.debug(e)

#                     for f in outputfiles:
#                         image_set.add(f)
#                     # s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(k[0], k[1], rt_enter_time[k], rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting),str(duration_task),str(pre_waiting),str(post_waiting))
#                     statstime[k] = [rt_enter_time[k], rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting),str(duration_task),str(pre_waiting),str(post_waiting)]


#                 # log_file.close()
#                 logging.debug('********************************************')
#                 logging.debug('Intermediate tasks :')
#                 logging.debug(statstime)
#                 logging.debug('********************************************')
#                 logging.debug("Communication time :")

#                 for item in image_set:
#                     timeseq = [(k[0],k[1],v) for k,v in statstime.items() if k[2]==item]
#                     timedict = {(x,y):v for x,y,v in timeseq}
#                     for key,value in timedict.items():
#                         task = key[0]
#                         last_task = key[1]
#                         if task=='master':
#                             try:
#                                 comm_time[(item,'datasource','master')] = timedict[('master','datasource')][0] - start_times[item]
#                             except Exception as e:
#                                 logging.debug('Error calculating datasource to master')
#                                 comm_time[(item,'datasource','master')] = 0
#                         elif task.startswith('lccdec'):
#                             try:
#                                 tasknum = task.split('lccdec')[1]
#                                 comm_time[(item, task,'home')] = end_times[item] - timedict[(task,'preagg'+tasknum)][2] 
#                             except Exception as e:
#                                 logging.debug('Error calculating lccdecoder to home - endtimes not ready')
#                                 comm_time[(item, task,'home')] = 0
#                         else:
#                             previous_info = [item for item in timedict if item[0] == last_task]
#                             try:
#                                 comm_time[(item, task,last_task)] = timedict[(task,last_task)][0]-timedict[previous_info[0]][2]    
#                             except Exception as e:
#                                 logging.debug('Error calculating task communication!!!')
#                                 comm_time[(item, task,last_task)] = 0

#                 logging.debug("****##########")
#                 logging.debug(comm_time)
#                 logging.debug("****####$$$$$$")
#                 logging.debug('********************************************') 
#     except Exception as e:
#         logging.debug("Bad reception or failed processing in Flask for runtime profiling")
#         logging.debug(e)
#         return "not ok"
#     return "ok"
# app.add_url_rule('/recv_runtime_profile', 'recv_runtime_profile', recv_runtime_profile)


#demo application
def recv_runtime_profile():
    """

    Receiving run-time profiling information for every task (task name, start time stats, waiting time stats, end time stats)
    
    Raises:
        Exception: failed processing in Flask
    """

    global rt_enter_time
    global rt_exec_time
    global rt_finish_time
    global rt_enter_task_time
    global rt_finish_task_time 

    try:
        logging.debug('Receive runtime stats information: ')
        worker_node = request.args.get('work_node')
        msg = request.args.get('msg').split()

        action = msg[0]
        from_task = msg[1]
        fname = msg[2]
        ts = float(msg[3])

        # logging.debug(msg)

        classlists = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard',  'lion', 'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
        classids = np.arange(0,len(classlists),1)
        classids = [str(x) for x in classids]
        classmap = dict(zip(classids,classlists))

        if '-' in fname:
            outputfile = fname.split('.')[0].split('-')
            logging.debug(outputfile)
            outputfiles = []
            logging.debug(classmap)
            for fi in outputfile:
                tmp = fi.split('#')[1]+'img'+ classmap[fi.split('#')[0]]+'.JPEG'
                outputfiles.append(tmp)
        else:
            outputfiles = [fname]

        # logging.debug(outputfiles)
        # logging.debug(from_task)
        # logging.debug(action)

        if action == 'rt_enter': # first file            
            for i in range(0,len(outputfiles)):
                if (worker_node,from_task,outputfiles[i]) in rt_enter_time:
                    logging.debug('Already exists enter...')
                    logging.debug(rt_enter_time[(worker_node,from_task,outputfiles[i])])
                    continue
                rt_enter_time[(worker_node,from_task,outputfiles[i])] = ts

            # logging.debug(rt_enter_time)
                
        elif action == 'rt_exec' : # first file            
            for i in range(0,len(outputfiles)):
                if (worker_node,from_task,outputfiles[i]) in rt_exec_time:
                    logging.debug('Already exists exec...')
                    logging.debug(rt_exec_time[(worker_node,from_task,outputfiles[i])])
                    continue
                rt_exec_time[(worker_node,from_task,outputfiles[i])] = ts
            # logging.debug(rt_exec_time)
        elif action == 'rt_enter_task' : # first file            
            for i in range(0,len(outputfiles)):
                if (worker_node,from_task,outputfiles[i]) in rt_enter_task_time:
                    logging.debug('Already exists enter task...')
                    logging.debug(rt_enter_task_time[(worker_node,from_task,outputfiles[i])])
                    continue
                rt_enter_task_time[(worker_node,from_task,outputfiles[i])] = ts
        elif action == 'rt_finish_task' : #last file            
            for i in range(0,len(outputfiles)): 
                rt_finish_task_time[(worker_node,from_task,outputfiles[i])] = ts                
        elif action == 'rt_finish' :#last file            
            for i in range(0,len(outputfiles)): 
                rt_finish_time[(worker_node,from_task,outputfiles[i])] = ts
            
            if worker_node in last_tasks:
                # Per task stats:
                logging.debug('********************************************') 
                logging.debug("Received final output at home: Runtime profiling info:")
                # logging.debug(outputfiles)
                """
                    - Worker node: task name
                    - Input file: input files
                    - Enter time: time the input file enter the queue
                    - Execute time: time the input file is processed
                    - Finish time: time the output file is generated
                    - Elapse time: total time since the input file is created till the output file is created
                    - Duration time: total execution time of the task
                    - Waiting time: total time since the input file is created till it is processed
                """
                log_file = open(os.path.join(os.path.dirname(__file__), 'runtime_tasks.txt'), "w")
                s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} \n".format('Task_name','From_task','local_input_file','Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time','Real execution time', 'Prewaiting')
                log_file.write(s)
                logging.debug(s)

                for k,v in rt_finish_time.items():
                    elaspe = 0
                    duration = 0
                    waiting = 0
                    duration_task = 0
                    pre_waiting = 0
                    # post_waiting = 0
                    try:
                        elapse = rt_finish_time[k]-rt_enter_time[k]  
                    except Exception as e:
                        rt_enter_time[k] = 0
                        logging.debug('no enter time')
                        logging.debug(e)

                    try:
                        duration = rt_finish_time[k]-rt_exec_time[k]
                    except Exception as e:
                        rt_exec_time[k] = 0
                        logging.debug('no exec time')
                        logging.debug(e)
                    
                    try:
                        waiting = rt_exec_time[k] - rt_enter_time[k]
                    except Exception as e:
                        logging.debug('no enter/exec time')
                        logging.debug(e)
                        
                    try:
                        # duration_task = rt_finish_task_time[k]-rt_enter_task_time[k]
                        duration_task = rt_finish_time[k]-rt_enter_task_time[k]
                    except Exception as e:
                        logging.debug('no finish/enter task time')
                        logging.debug(e)

                    try:
                        pre_waiting = rt_enter_task_time[k] - rt_enter_time[k] 
                    except Exception as e:
                        logging.debug('no enter/enter task time')
                        logging.debug(e)

                    # try:
                    #     post_waiting = rt_finish_time[k] - rt_finish_task_time[k]#not yet know why
                    #     if post_waiting<0: 
                    #         post_waiting = 0
                    # except Exception as e:
                    #     logging.debug('no finish/finish task time')
                    #     logging.debug(e)

                    for f in outputfiles:
                        image_set.add(f)
                    # s = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}\n".format(k[0], k[1], rt_enter_time[k], rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting),str(duration_task),str(pre_waiting),str(post_waiting))
                    statstime[k] = [rt_enter_time[k], rt_exec_time[k],rt_finish_time[k],str(elapse),str(duration),str(waiting),str(duration_task),str(pre_waiting)]


                # log_file.close()
                logging.debug('********************************************')
                logging.debug('Intermediate tasks :')
                logging.debug(statstime)
                logging.debug('********************************************')
                logging.debug("Communication time :")

                for item in image_set:
                    timeseq = [(k[0],k[1],v) for k,v in statstime.items() if k[2]==item]
                    timedict = {(x,y):v for x,y,v in timeseq}
                    for key,value in timedict.items():
                        task = key[0]
                        last_task = key[1]
                        if task=='master':
                            try:
                                comm_time[(item,'datasource','master')] = timedict[('master','datasource')][0] - start_times[item]
                            except Exception as e:
                                logging.debug('Error calculating datasource to master')
                                comm_time[(item,'datasource','master')] = 0
                        elif task.startswith('lccdec'):
                            try:
                                tasknum = task.split('lccdec')[1]
                                comm_time[(item, task,'home')] = end_times[item] - timedict[(task,'preagg'+tasknum)][2] 
                            except Exception as e:
                                logging.debug('Error calculating lccdecoder to home - endtimes not ready')
                                comm_time[(item, task,'home')] = 0
                        else:
                            previous_info = [item for item in timedict if item[0] == last_task]
                            try:
                                comm_time[(item, task,last_task)] = timedict[(task,last_task)][0]-timedict[previous_info[0]][2]    
                            except Exception as e:
                                logging.debug('Error calculating task communication!!!')
                                comm_time[(item, task,last_task)] = 0

                logging.debug("****##########")
                logging.debug(comm_time)
                logging.debug("****####$$$$$$")
                logging.debug('********************************************') 
    except Exception as e:
        logging.debug("Bad reception or failed processing in Flask for runtime profiling")
        logging.debug(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_runtime_profile', 'recv_runtime_profile', recv_runtime_profile)



class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        logging.debug("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)

def transfer_data_scp(ID,user,pword,source, destination):
    """Transfer data using SCP
    
    Args:
        IP (str): destination ID
        user (str): username
        pword (str): password
        source (str): source file path
        destination (str): destination file path
    """
    #Keep retrying in case the containers are still building/booting up on
    #the child nodes
    retry = 0
    ts = -1
    while retry < num_retries:
        try:
            nodeIP = combined_ip_map[ID]
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" % (pword, ssh_port, source, user, nodeIP, destination)
            os.system(cmd)
            logging.debug('data transfer complete\n')
            ts = time.time()
            # ts = datetime.utcnow()
            s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home', transfer_type,source,ts)
            runtime_sender_log.write(s)
            runtime_sender_log.flush()
            break
        except:
            logging.debug('profiler_worker.txt: SSH Connection refused or File transfer failed, will retry in 2 seconds')
            time.sleep(2)
            retry += 1
    if retry == num_retries:
        s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,source,ts)
        runtime_sender_log.write(s)
        runtime_sender_log.flush()

    

def transfer_data(ID,user,pword,source, destination):
    """Transfer data with given parameters
    
    Args:
        IP (str): destination ID 
        user (str): destination username
        pword (str): destination password
        source (str): source file path
        destination (str): destination file path
    """
    msg = 'Transfer to ID: %s , username: %s , password: %s, source path: %s , destination path: %s'%(ID,user,pword,source, destination)
    # logging.debug(msg)
    

    if TRANSFER == 0:
        return transfer_data_scp(ID,user,pword,source, destination)

    return transfer_data_scp(ID,user,pword,source, destination) #default


# class MyHandler(pyinotify.ProcessEvent):
#     """Setup the event handler for all the events
#     """


#     def process_IN_CLOSE_WRITE(self, event):
#         """On every node, whenever there is scheduling information sent from the central network profiler:
#             - Connect the database
#             - Scheduling measurement procedure
#             - Scheduling regression procedure
#             - Start the schedulers
        
#         Args:
#             event (ProcessEvent): a new file is created
#         """

#         global start_times, end_times
#         global exec_times
#         global count

#         logging.debug("Received file as output - %s." % event.pathname) 
#         outputfile = event.pathname.split('/')[-1].split('_')[0]
#         logging.debug(outputfile)
#         t = datetime.utcnow()
#         end_times[outputfile] = unix_time(t)
        
#         exec_times[outputfile] = end_times[outputfile] - start_times[outputfile]
#         logging.debug("execution time is: %s", exec_times)

#         if BOKEH == 2: #used for combined_app with distribute script
#             app_name = outputfile.split('-')[0]
#             msg = 'makespan '+ app_name + ' '+ outputfile+ ' '+ str(exec_times[outputfile]) 
#             demo_help(BOKEH_SERVER,BOKEH_PORT,app_name,msg)

#         if BOKEH == 3:
#             msg = 'makespan ' + appoption + ' ' + appname + ' '+ outputfile+ ' '+ str(exec_times[outputfile]) + '\n'
#             demo_help(BOKEH_SERVER,BOKEH_PORT,appoption,msg)


# Demo application
class MyHandler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        """On every node, whenever there is scheduling information sent from the central network profiler:
            - Connect the database
            - Scheduling measurement procedure
            - Scheduling regression procedure
            - Start the schedulers
        
        Args:
            event (ProcessEvent): a new file is created
        """

        global start_times, end_times
        global exec_times
        global count


        logging.debug("Received file as output - %s." % event.pathname) 
        outfile =  event.pathname.split('.')[0].split('/')[-1].split('_')[-1]
        outputfile =outfile.split('-')
        logging.debug(outputfile)

        classlists = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard',  'lion', 'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
        classids = np.arange(0,len(classlists),1)
        classids = [str(x) for x in classids]
        classmap = dict(zip(classids,classlists))

        for fi in outputfile:
            tmpfile = fi.split('#')[1]+'img'+ classmap[fi.split('#')[0]]+'.JPEG'
            logging.debug(tmpfile)
            t = time.time()
            if not (tmpfile in files_out_set):
                logging.debug('Received time %f',t)
                end_times[tmpfile] = t
                try:
                    exec_times[tmpfile] = end_times[tmpfile] - start_times[tmpfile]
                except Exception as e:
                    logging.debug('Could not find the start time information for the file!!!!')
                    logging.debug(f)
                logging.debug("execution time is: %s", exec_times)

        

    
class Handler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        """On every node, whenever there is scheduling information sent from the central network profiler:
            - Connect the database
            - Scheduling measurement procedure
            - Scheduling regression procedure
            - Start the schedulers
        
        Args:
            event (ProcessEvent): a new file is created
        """
        global start_times, end_times

        logging.debug("Received file as input - %s." % event.pathname)  

        if RUNTIME == 1:   
            ts = time.time() 
            # ts = datetime.now()
            # ts = unix_time(ts)
            s = "{:<10} {:<10} {:<10} {:<10} \n".format('CIRCE_home',transfer_type,event.pathname,ts)
            runtime_receiver_log.write(s)
            runtime_receiver_log.flush()



        inputfile = event.pathname.split('/')[-1]
        logging.debug(inputfile)
        if not (inputfile in files_in_set): 
            t = time.time()
            # t = datetime.now()
            start_times[inputfile] = t
            logging.debug('Received time %f',t)
            new_file_name = os.path.split(event.pathname)[-1]


            #This part should be optimized to avoid hardcoding IP, user and password
            #of the first task node
            # IP = os.environ['CHILD_NODES_IPS']
            ID = os.environ['CHILD_NODES']
            source = event.pathname
            destination = os.path.join('/centralized_scheduler', 'input', new_file_name)
            transfer_data(ID,username, password,source, destination)

def main():
    """
        -   Read configurations (DAG info, node info) from ``nodes.txt`` and ``configuration.txt``
        -   Monitor ``INPUT`` folder for the incoming files
        -   Whenever there is a new file showing up in ``INPUT`` folder, copy the file to the ``INPUT`` folder of the first scheduled node.
        -   Collect execution profiling information from the system.
    """
    global logging
    logging.basicConfig(level = logging.DEBUG)


    INI_PATH = 'jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    # Prepare transfer-runtime file:
    global runtime_sender_log, RUNTIME,TRANSFER, transfer_type, appname,appoption

    RUNTIME = int(config['CONFIG']['RUNTIME'])
    TRANSFER = int(config['CONFIG']['TRANSFER'])
    appname = os.environ['APPNAME']
    appoption = os.environ['APPOPTION']

    if TRANSFER == 0:
        transfer_type = 'scp'

    runtime_sender_log = open(os.path.join(os.path.dirname(__file__), 'runtime_transfer_sender.txt'), "w")
    s = "{:<10} {:<10} {:<10} {:<10} \n".format('Node_name', 'Transfer_Type', 'File_Path', 'Time_stamp')
    runtime_sender_log.write(s)
    runtime_sender_log.close()
    runtime_sender_log = open(os.path.join(os.path.dirname(__file__), 'runtime_transfer_sender.txt'), "a")
    #Node_name, Transfer_Type, Source_path , Time_stamp

    if RUNTIME == 1:
        global runtime_receiver_log
        runtime_receiver_log = open(os.path.join(os.path.dirname(__file__), 'runtime_transfer_receiver.txt'), "w")
        s = "{:<10} {:<10} {:<10} {:<10} \n".format('Node_name', 'Transfer_Type', 'File_path', 'Time_stamp')
        runtime_receiver_log.write(s)
        runtime_receiver_log.close()
        runtime_receiver_log = open(os.path.join(os.path.dirname(__file__), 'runtime_transfer_receiver.txt'), "a")
        #Node_name, Transfer_Type, Source_path , Time_stamp

    global FLASK_DOCKER, username, password, ssh_port, num_retries

    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    ssh_port    = int(config['PORT']['SSH_SVC'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])

    global combined_ip_map
    combined_ip_map = dict()
    combined_ip_map[os.environ['CHILD_NODES']]= os.environ['CHILD_NODES_IPS']

    path1 = 'configuration.txt'
    path2 = 'nodes.txt'
    dag_info = read_config(path1,path2)
    

    global manager
    manager = Manager()

    global start_times, end_times, exec_times
    start_times = manager.dict()
    end_times = manager.dict()
    exec_times = manager.dict()
    
    global dag,count, start_time,end_time, rt_enter_time, rt_exec_time, rt_finish_time, files_in_set, files_out_set, rt_enter_task_time,rt_finish_task_time
    count = 0
    # start_time = defaultdict(list)
    # end_time = defaultdict(list)

    # rt_enter_time = defaultdict(list)
    # rt_exec_time = defaultdict(list)
    # rt_finish_time = defaultdict(list)
    # rt_enter_task_time = defaultdict(list)
    # rt_finish_task_time = defaultdict(list)
    start_time = manager.dict()
    end_time = manager.dict()

    rt_enter_time = manager.dict()
    rt_exec_time = manager.dict()
    rt_finish_time = manager.dict()
    rt_enter_task_time = manager.dict()
    rt_finish_task_time = manager.dict()

    files_in_set = set()
    files_out_set = set()


    #get DAG and home machine info
    first_task = dag_info[0]
    dag = dag_info[1]
    hosts=dag_info[2]

    global statstime, image_set, comm_time
    statstime = manager.dict()
    image_set = set()
    comm_time = manager.dict()

    global last_tasks
    last_tasks = set()
    for task in dag_info[1]:
        if 'home' in dag_info[1][task]:
            last_tasks.add(task)

    logging.debug('Last tasks')
    logging.debug(last_tasks)

    global last_tasks_map
    last_tasks_map = dict()

    for task in dag:
        for last_task in dag[task][2:]:
            if last_task not in last_tasks_map:
                last_tasks_map[last_task] = [task]
            else:    
                last_tasks_map[last_task].append(task)

    last_tasks_map['master'] = ['datasource']

    logging.debug('Last task map')
    logging.debug(last_tasks_map)

    


    global BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH_SERVER = config['BOKEH_LIST']['BOKEH_SERVER']
    BOKEH_PORT = int(config['BOKEH_LIST']['BOKEH_PORT'])
    BOKEH = int(config['BOKEH_LIST']['BOKEH'])

    web_server = MonitorRecv()
    web_server.start()

    # watch manager
    wm = pyinotify.WatchManager()
    input_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'input/')
    wm.add_watch(input_folder, pyinotify.ALL_EVENTS, rec=True)
    logging.debug('starting the input monitoring process\n')
    eh = Handler()
    notifier = pyinotify.ThreadedNotifier(wm, eh)
    notifier.start()

    output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'output/')
    wm1 = pyinotify.WatchManager()
    wm1.add_watch(output_folder, pyinotify.ALL_EVENTS, rec=True)
    logging.debug('starting the output monitoring process\n')
    eh1 = MyHandler()
    notifier1= pyinotify.Notifier(wm1, eh1)
    notifier1.loop()
    
    
if __name__ == '__main__':

    main()
