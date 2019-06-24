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
import datetime
from flask import Flask, request


# N = 500
folder = 'test/'
# if os.path.isdir(folder):
#     shutil.rmtree(folder)
# os.mkdir(folder)


# class Test():
#     def __init__(self,ID):
#         self.ID = ID
#         self.file = None
#         self.test()
#     def test(self):
#         print(self.ID)
#         path = folder+str(self.ID)+'.log'
#         self.file = open(path,'w')
#         self.file.write('Testing')
#         time.sleep(30)
#         self.file.close()
        


# # Test threads       
# for i in range(0,N):
#   _thread.start_new_thread(Test,(i,))
# doc = curdoc()
# doc.title = 'Users management'
# ti = 'Subscriber Information'
# title1 = Div(text=ti,style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=400, height=20)
# p1 = layout([title1])
# layout = row(p1)
# doc.add_root(layout)

count = 0

class subscriber():
    def __init__(self,ID):
        self.id = ID
        self.file = None
        self.client = mqtt.Client(str(ID))
        print(self.client)
        # self.server = '128.125.124.40'
        # self.port = 60236
        self.server = '127.0.0.1'
        self.port = 1883 
        self.timeout = 500
        self.username = 'anrgusc'
        self.password = 'anrgusc'
        self.client.username_pw_set(self.username,self.password)
        self.client.connect(self.server, self.port, self.timeout)
        self.client.on_connect = self.on_connect
        # self.client.on_message = self.on_message
        self.client.loop_forever()
    def on_connect(self,client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        if rc==0:
            print("connected OK Returned code=",rc)
            # subres = client.subscribe('test',qos=1)
            path = folder+str(self.id)+'.log'
            self.file = open(path,'a')
            self.file.write('Testing')
            self.file.write('\n')
            time.sleep(20)
            self.file.close()
            
        else:
            print("Bad connection Returned code=",rc)
            time.sleep(20)
    # def on_message(self,client, userdata, msg):
    #     message = msg.payload.decode()
    #     path = folder+str(self.id)+'.log'
    #     self.file = open(path,'a')
    #     self.file.write(message)
    #     self.file.write('\n')
    #     time.sleep(20)
    #     self.file.close()
       
    

    


app = Flask(__name__)
# Test MQTT
def main():
    N = 500
    for i in range(250,N):
        print(i)
        s = _thread.start_new_thread(subscriber,(i,))
        time.sleep(3)

    print(count)
    app.run(host='0.0.0.0',port=5056)

if __name__ == '__main__':
    main()





