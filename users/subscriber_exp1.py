__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

"""
    Experiment 1 : 100 nodes, 1 DAG 100 tasks, 500 users, 5 users subscribe to the results of each task of the same DAG 
"""

import os
from tornado import gen
from functools import partial
from bokeh.models import Button, NumeralTickFormatter
from bokeh.palettes import RdYlBu3
from bokeh.plotting import *
from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, Label, Arrow, NormalHead, LabelSet, HoverTool
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.io import output_file, show
from bokeh.layouts import row,column
from bokeh.models import ColumnDataSource, ColorBar
from bokeh.palettes import brewer
from bokeh.transform import linear_cmap
from bokeh.layouts import widgetbox,layout
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.models.widgets import MultiSelect, Select, Div
from bokeh.models import Label
from datetime import date
from datetime import datetime
from random import randint
import paho.mqtt.client as mqtt
import time
import numpy as np 
from itertools import cycle, islice
import random
import pandas as pd
import datetime
import collections
from pytz import timezone
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool, BoxZoomTool, ResetTool
from bokeh.models.graphs import from_networkx
from bokeh.transform import transform 
from bokeh.models.transforms import CustomJSTransform 
import _thread
import shutil
from flask import Flask, request

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
    def __init__(self,outfname,ID,path,subs,server,port,timeout,looptimeout,user_log):
        # self.OUTFNAME = outfname
        self.id = ID
        self.path = path
        self.subs = subs
        self.server = server
        self.port = port
        self.timeout = timeout
        self.looptimeout = looptimeout
        # self.outf = open(OUTFNAME,'a')
        self.client = mqtt.Client()
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



global OUTFNAME, SERVER_IP, DAG_PATH, EXP,folder
OUTFNAME = 'users_management.html'
SERVER_IP = "127.0.0.1"
DAG_PATH = '../app_specific_files/dummy_app_100/configuration.txt'
EXP = 'Experiment 1'
folder = 'exp1'

global tasks,taskid,userid,usertask
tasks,tasksid = retrieve_tasks(DAG_PATH)
N = len(tasks)
M = 5
cid = 1
userid = []
usertask = []
if os.path.isdir(folder):
    shutil.rmtree(folder)
for i in range(1,N+1):
    cur_task = tasksid[i]
    for j in range(0,M):
        user_path = '%s/user%d'%(folder,cid)
        user_log = '%s/user%d/user%d.log'%(folder,cid,cid)
        user_id = 'U'+str(cid)
        cur_sub = cur_task
        userid.append(user_id)
        usertask.append(cur_task)
        if not os.path.isdir(user_path):
            os.makedirs(user_path, exist_ok=True)
        _thread.start_new_thread(subscriber,(OUTFNAME,cid,user_path,cur_sub,SERVER_IP,1883,300,1,user_log))
        cid = cid+1


app.run(host='0.0.0.0',port=5055)

#####################
global doc, data_table,source
print(userid)
print(usertask)
source = ColumnDataSource(dict(user_id=userid,topics=usertask))
columns = [TableColumn(field="user_id", title="User ID"),TableColumn(field="topics", title="Topics")]
data_table = DataTable(source=source, columns=columns, width=1000, height=1000,selectable=True)
ti = '%s - Subscriber Information'%(EXP)
title1 = Div(text=ti,style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=400, height=20)
#####################

doc = curdoc()
doc.title = 'Users management'
p1 = layout([title1,widgetbox(data_table,width=1000,height=1000)])
layout = row(p1)
doc.add_root(layout) 