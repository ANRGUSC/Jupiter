__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

"""
    Experiment 1 : 100 nodes, 1 DAG 100 tasks, 500 users, 5 users subscribe to the results of each task of the same DAG 
"""

import os
import _thread
import shutil
from flask import Flask, request
import paho.mqtt.client as mqtt
import time

app = Flask(__name__)
    
def retrieve_tasks(dag_info_file):
    config_file = open(dag_info_file,'r')
    dag_size = int(config_file.readline())

    tasks={}
    tasksid={}
    for i, line in enumerate(config_file, 1):
        dag_line = line.strip().split(" ")
        tasks[dag_line[0]]=i 
        tasksid[i]=dag_line[0]
        if i == dag_size:
            break
    
    return tasks,tasksid

class subscriber():
    def __init__(self,ID,path,subs,server,port,timeout,looptimeout,user_log):
        self.id = ID
        self.path = path
        self.subs = subs
        self.server = server
        self.port = port
        self.timeout = timeout
        self.looptimeout = looptimeout
        self.client = mqtt.Client()
        self.username = 'anrgusc'
        self.password = 'anrgusc'
        self.client.username_pw_set(self.username,self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.server, self.port, self.timeout)
        self.user_log = user_log
        self.client.loop_forever()
        
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self,client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        subres = client.subscribe(self.subs,qos=1)
        print("Connected with result code "+str(rc))
        

    def on_message(self,client, userdata, msg):
        message = msg.payload.decode()
        print('--------------')
        print(message)
        print('--------------')
        with open(self.user_log,'a') as f:
            f.write(message)
            f.write('\n')
            time.sleep(20)





if __name__ == '__main__':
    

    global SERVER_IP, DAG_PATH, folder
    SERVER_IP = "127.0.0.1"
    DAG_PATH = '../app_specific_files/dummy_app_100/configuration.txt'
    folder = 'exp1'

    global tasks,taskid
    tasks,tasksid = retrieve_tasks(DAG_PATH)
    N = int(len(tasks)/2)
    M = 5
    cid = 1
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.mkdir(folder)
    for i in range(1,N+1):
        cur_task = tasksid[i]
        for j in range(0,M):
            user_path = '%s/user%d'%(folder,cid)
            user_log = '%s/user%d/user%d.log'%(folder,cid,cid)
            cur_sub = cur_task
            if not os.path.isdir(user_path):
                os.makedirs(user_path, exist_ok=True)
            _thread.start_new_thread(subscriber,(cid,user_path,cur_sub,SERVER_IP,1883,300,1,user_log))
            cid = cid+1

    app.run(host='0.0.0.0',port=5055)