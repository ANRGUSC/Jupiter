__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

"""
    Experiment 67: collect overhead latency and power overhead (CPU & memory)
"""

import sys
import os
import _thread
import shutil
from flask import Flask, request
import paho.mqtt.client as mqtt
import time
sys.path.append("../")
import jupiter_config

app = Flask(__name__)
    
def k8s_get_nodes(node_info_file):
    """read the node info from the file input
  
    Args:
        node_info_file (str): path of ``node.txt``
  
    Returns:
        dict: node information 
    """

    nodes = {}
    node_file = open(node_info_file, "r")
    for i,line in enumerate(node_file):
        node_line = line.strip().split(" ")
        nodes[node_line[0]] = node_line[1]   
    return nodes

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

class collector(): # collect power overhead (CPU/memory)
    def __init__(self,ID,subs,server,port,timeout,looptimeout,node_log):
        self.id = ID
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
        self.node_log = node_log
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
        with open(self.node_log,'a+') as f:
            f.write(message)





if __name__ == '__main__':
    

    jupiter_config.set_globals()

    global SERVER_IP, DAG_PATH, folder
    SERVER_IP = "127.0.0.1"
    NODE_PATH = jupiter_config.HERE + 'nodes.txt'
    nodes = k8s_get_nodes(NODE_PATH)
    
    N = len(nodes)
    DAG_PATH = jupiter_config.APP_PATH + 'configuration.txt'
    tasks,tasksid = retrieve_tasks(DAG_PATH)
    M = len(tasks)

    main_folder = '../stats/exp8_data'
    folder_list= ['makespan','msg_overhead','power_overhead','mapping_latency','summary_latency']
    try:
        os.mkdir(main_folder)
        for folder in folder_list:
            exp_folder= main_folder+'/'+folder
            os.mkdir(exp_folder)
    except:
        print('Folder already existed')

    
    try:
        for folder in folder_list:
            if folder!='summary_latency':
                task_folder = main_folder+'/'+folder+'/N%dM%d'%(N,M)
                os.mkdir(task_folder)
    except:
        print('Subfolder already existed')

    if jupiter_config.PRICING == 0:
        if jupiter_config.SCHEDULER == 0:
            option = 'nonpricing_heft'
        elif jupiter_config.SCHEDULER == 2:
            option = 'nonpricing_wave'
        else:
            option = 'others'
    elif jupiter_config.PRICING == 1:
        option = 'pricing_push'
    elif jupiter_config.PRICING == 2:
        option = 'pricing_event'
    elif jupiter_config.PRICING == 3:
        option = 'pricing_integrated'
    elif jupiter_config.PRICING == 4:
        option = 'pricing_decoupled'

    print(option)

    mqtt_port = 1883
    mqtt_timeout = 300

    # Collect makespan
    exp_folder = main_folder+'/'+folder_list[0]
    makespan_log = '%s/N%dM%d/%s_N%d_M%d.log'%(exp_folder,N,M,option,N,M)
    cur_app = jupiter_config.APP_OPTION
    _thread.start_new_thread(collector,(cur_app,cur_app,SERVER_IP,mqtt_port,mqtt_timeout,1,makespan_log))
    
    # Collect power overhead (CPU/ memory)
    exp_folder = main_folder+'/'+folder_list[2]
    for node in nodes:
        node_log = '%s/N%dM%d/%s_%s_N%d_M%d.log'%(exp_folder,N,M,option,node,N,M)
        cur_sub = 'poweroverhead_%s'%(node)
        print(cur_sub)
        _thread.start_new_thread(collector,(node,cur_sub,SERVER_IP,mqtt_port,mqtt_timeout,1,node_log))


    ## Collect message overhead # nonpricing
    # exp_folder = main_folder+'/'+folder_list[1]
    # for node in nodes:
    #     node_log = '%s/N%dM%d/%s_%s_N%d_M%d.log'%(exp_folder,N,M,option,node,N,M)
    #     cur_sub = 'msgoverhead_%s'%(node)
    #     print(cur_sub)
    #     _thread.start_new_thread(collector,(node,cur_sub,SERVER_IP,mqtt_port,mqtt_timeout,1,node_log))

    ## Collect message overhead # pricing
    exp_folder = main_folder+'/'+folder_list[1] 
    for node in nodes:
        node_log = '%s/N%dM%d/%s_%s_N%d_M%d'%(exp_folder,N,M,option,node,N,M)
        cur_sub = 'msgoverhead_%s'%(node)
        print(cur_sub)
        print(node_log)
        _thread.start_new_thread(collector,(node,cur_sub,SERVER_IP,mqtt_port,mqtt_timeout,1,node_log))
    # for task in tasks:
    #     task_log = '%s/N%dM%d/%s_controller%s_N%d_M%d.log'%(exp_folder,N,M,option,task,N,M)
    #     cur_sub = 'msgoverhead_controller%s'%(task)
    #     print(cur_sub)
    #     print(task_log)
    #     _thread.start_new_thread(collector,(task,cur_sub,SERVER_IP,mqtt_port,mqtt_timeout,1,task_log))

    # Collect mapping latency 
    # exp_folder = main_folder+'/'+folder_list[3]
    # mapping_log = '%s/N%dM%d/%s_N%d_M%d.log'%(exp_folder,N,M,option,N,M)
    # print(mapping_log)
    # cur_app = jupiter_config.APP_OPTION
    # cur_sub = 'mappinglatency_%s'%(cur_app)
    # print(cur_sub)
    # # SERVER_IP = '192.168.1.234'
    # _thread.start_new_thread(collector,(cur_app,cur_sub,SERVER_IP,mqtt_port,mqtt_timeout,1,mapping_log))



    app.run(host='0.0.0.0',port=5055)