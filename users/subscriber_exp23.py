__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

"""
    Experiment 2: 100 nodes, 100 DAGs, 100 users, each user subscribe to the final make span result of each DAG 
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



#bokeh serve --show subscriber_exp23.py
def get_app_list(app_path_list):
    app_option = []
    dir_list = next(os.walk(app_path_list))[1]
    for d in dir_list:
        app_option.append(d)

    return app_option
    

class subscriber():
    def __init__(self,ID,path,subs,server,port,timeout,looptimeout,user_log):
        self.id = ID
        self.path = path
        self.subs = subs
        self.server = server
        self.port = port
        self.timeout = timeout
        self.looptimeout = looptimeout
        self.user_log = user_log
        self.file = None
        self.client = mqtt.Client(str(ID))
        self.client.connect(self.server, self.port, self.timeout)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.loop_forever()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self,client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        if rc==0:
            print("connected OK Returned code=",rc)
        else:
            print("Bad connection Returned code=",rc)
        subres = client.subscribe(self.subs,qos=1)
        # print("Starting to write results to file")
        # self.file = open(self.user_log,'w')
        

    def on_message(self,client, userdata, msg):
        message = msg.payload.decode()
        print('--------------')
        print(message)
        print('--------------')
        with open(self.user_log,'a') as f:
            f.write(message)
            f.write('\n')



global OUTFNAME, SERVER_IP, EXP, folder,APP_PATH_LIST
OUTFNAME = 'users_management.html'
SERVER_IP = "127.0.0.1"
EXP = 'Experiment 3'
folder = 'exp3'
M = 5
#EXP = 'Experiment 3'
#folder = 'ex3'
#M = 2

APP_PATH_LIST = '../app_specific_files/dummy_app_combined/dummy_app_list'

global userid,userapp,app_options
app_options = get_app_list(APP_PATH_LIST)

print(app_options)

N = len(app_options)
cid = 1
userid = []
userapp = []
if os.path.isdir(folder):
    shutil.rmtree(folder)
for i in range(1,N+1):
    cur_app = 'dummyapp%d'%(i)
    for j in range(0,M):
        user_path = '%s/user%d'%(folder,cid)
        user_log = '%s/user%d/user%d.log'%(folder,cid,cid)
        user_id = 'U'+str(cid)
        print(cid)
        cur_sub = cur_app
        userid.append(user_id)
        userapp.append(cur_app)
        if not os.path.isdir(user_path):
            os.makedirs(user_path, exist_ok=True)
        info = _thread.start_new_thread(subscriber,(cid,user_path,cur_sub,SERVER_IP,1883,300,1,user_log))
        time.sleep(1)
        print(info)
        cid = cid+1


#####################
global doc, data_table,source
print(userid)
print(userapp)
source = ColumnDataSource(dict(user_id=userid,topics=userapp))
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


