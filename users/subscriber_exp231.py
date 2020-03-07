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
from flask import Flask, request

app = Flask(__name__)

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

    global OUTFNAME, SERVER_IP, EXP, folder,APP_PATH_LIST
    OUTFNAME = 'users_management.html'
    SERVER_IP = "127.0.0.1"

    EXP = 'Experiment 3'
    folder = 'exp3'
    M = 5

    APP_PATH_LIST = '../app_specific_files/dummy_app_combined/dummy_app_list'

    global userid,userapp,app_options
    app_options = get_app_list(APP_PATH_LIST)

    N = int(len(app_options)/2)
    
    cid = 1
    
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    for i in range(1,N+1):
        cur_app = 'dummyapp%d'%(i)
        for j in range(0,M):
            user_path = '%s/user%d'%(folder,cid)
            user_log = '%s/user%d/user%d.log'%(folder,cid,cid)
            user_id = 'U'+str(cid)
            cur_sub = cur_app
            
            if not os.path.isdir(user_path):
                os.makedirs(user_path, exist_ok=True)
            info = _thread.start_new_thread(subscriber,(cid,user_path,cur_sub,SERVER_IP,1883,300,1,user_log))
            time.sleep(1)
            cid = cid+1


    app.run(host='0.0.0.0',port=5055)


