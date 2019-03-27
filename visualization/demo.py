__author__ = "Quynh Nguyen, Aleksandra Knezevic and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

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
from random import randint
import paho.mqtt.client as mqtt
import time
import numpy as np 
from itertools import cycle, islice
import random
import pandas as pd
import datetime
import collections


class mq():


    def __init__(self,outfname,subs,server,port,timeout,looptimeout):
        self.OUTFNAME = outfname
        self.subs = subs
        self.server = server
        self.port = port
        self.timeout = timeout
        self.looptimeout = looptimeout
        self.outf = open(OUTFNAME,'a')
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.server, self.port, self.timeout)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self,client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        subres = client.subscribe(self.subs,qos=1)
        print("Connected with result code "+str(rc))


    # The callback for when a PUBLISH message is received from the server.
    def on_message(self,client, userdata, msg):
        start_messages = ['localpro starts', 'aggregate0 starts', 'aggregate1 starts', 'aggregate2 starts',
        'simpledetector0 starts', 'simpledetector1 starts', 'simpledetector2 starts', 'astutedetector0 starts',
        'astutedetector1 starts', 'astutedetector2 starts', 'fusioncenter0 starts', 'fusioncenter1 starts', 
        'fusioncenter2 starts', 'globalfusion starts']

        end_messages = ['localpro ends', 'aggregate0 ends', 'aggregate1 ends', 'aggregate2 ends',
        'simpledetector0 ends', 'simpledetector1 ends', 'simpledetector2 ends', 'astutedetector0 ends',
        'astutedetector1 ends', 'astutedetector2 ends', 'fusioncenter0 ends', 'fusioncenter1 ends', 
        'fusioncenter2 ends', 'globalfusion ends']


        top_dag=[5.15, 4.15, 4.15, 4.15, 3.15, 3.15, 3.15, 3.15, 3.15, 3.15, 2.15,2.15,2.15,1.15]
        bottom_dag=[4.85, 3.85,3.85,3.85, 2.85,2.85,2.85,2.85,2.85,2.85, 1.85,1.85,1.85, 0.85]
        left_dag= [3.3,1.3,3.3,5.3, 0.8, 1.8, 2.8, 3.8, 4.8,5.8, 1.3,3.3,5.3,3.3]
        right_dag=[3.7,1.7,3.7,5.7, 1.2, 2.2, 3.2, 4.2, 5.2, 6.2,1.7,3.7,5.7,3.7]


        top = [4,4,4,4,4,4,4,2,2,2,2,2,2,2]
        bottom = [2,2,2,2,2,2,2,0,0,0,0,0,0,0]
        left = [0,1,2,3,4,5,6,0,1,2,3,4,5,6]
        right = [1,2,3,4,5,6,7,1,2,3,4,5,6,7]

        message = msg.payload.decode()
        global start_time
        global finish_time
        global total_time

        print('--------------')
        print(message)
        print('--------------')
        if message in start_messages:

            if message == 'localpro starts':
                new_time =  time.time()
                start_time.append(new_time)

            index = start_messages.index(message)
            top,bottom,left,right = top[index],bottom[index],left[index],right[index]
            topd,bottomd,leftd,rightd = top_dag[index],bottom_dag[index],left_dag[index],right_dag[index]

            color = "red"
            doc.add_next_tick_callback(partial(update3, top= topd, bottom=bottomd,left=leftd,right=rightd, color=color))
            #doc.add_next_tick_callback(partial(update1, top=top, bottom=bottom,left=left, right=right,color=color))
            

        elif message in end_messages:

            if message == 'global_fusion ends':
                finish_time = time.time()
                total_time = (finish_time - start_time.pop(0))/60
                global offset
                global input_num
                print("TOTAL_TIME: ", total_time, " minutes")

                #doc.add_next_tick_callback(partial(update2, x=7.5, y=3.2-offset, time = 'in'+str(input_num)+": "+str(format(total_time, '.4f') + ' min')))
                offset = offset + 0.2
                input_num = input_num+1


            index = end_messages.index(message)
            top,bottom,left,right = top[index],bottom[index],left[index],right[index]
            topd,bottomd,leftd,rightd = top_dag[index],bottom_dag[index],left_dag[index],right_dag[index]


            color=['#C2D2F9',"#5984E8","#5984E8","#5984E8","#9380F0","#9380F0","#9380F0",
            "#1906BF","#1906BF","#1906BF", '#084594','#084594','#084594',"#33148E"]
            color1=["#C2D2F9","#5984E8","#5984E8","#5984E8","#9380F0","#1906BF","#9380F0",
            "#1906BF","#9380F0","#1906BF","#084594","#084594","#084594","#33148E"]

            doc.add_next_tick_callback(partial(update3, top= topd, bottom=bottomd,left=leftd,right=rightd, color=color1[index]))
            #doc.add_next_tick_callback(partial(update1, top=top, bottom=bottom,left=left, right=right,color=color[index]))

        elif message.startswith('mapping'):
            print('---- Receive task mapping')
            doc.add_next_tick_callback(partial(update5,new=message,old=source6_df,attr=source6.data))
            doc.add_next_tick_callback(partial(update4,new=message,old=source5_df,attr=data_table2.source))

def retrieve_tasks(dag_info_file):
    config_file = open(dag_info_file,'r')
    dag_size = int(config_file.readline())

    tasks={}
    for i, line in enumerate(config_file, 1):
        dag_line = line.strip().split(" ")
        tasks[dag_line[0]]=i 
        if i == dag_size:
            break
    return tasks

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
        nodes[i] = [node_line[0],node_line[1]]    
    return nodes


def repeatlist(it, count):
    return islice(cycle(it), count)

def update():
    m.client.loop(timeout=0.5)

# @gen.coroutine
# def update1(top,bottom,right,left,color):
#     source.stream(dict(top=[top], bottom=[bottom],left=[left],right=[right],color=[color],line_color=["black"], line_width=[2]))

@gen.coroutine
def update2(x,y,time):
    source1.stream(dict(x=[x], y=[y], time=[time], text_font_style= ['bold']))

@gen.coroutine
def update3(top,bottom,left,right,color):
    source2.stream(dict(top=[top], bottom=[bottom],left=[left],right=[right],color=[color]))

@gen.coroutine
def update4(attr, old, new):
    assigned_info = new.split(' ')[1:]
    for info in assigned_info:
        tmp = info.split(':')
        new_source5_df.loc[new_source5_df.task_names==tmp[0],'assigned']=tmp[1]
        new_source5_df.loc[new_source5_df.task_names==tmp[0],'as_time']=datetime.datetime.fromtimestamp(float(tmp[2])).strftime("%d.%m.%y %H:%M:%S")

    source5.data = {
        'task_id'       : new_source5_df.task_id,
        'task_names'    : new_source5_df.task_names,
        'assigned'      : new_source5_df.assigned,
        'as_time'       : new_source5_df.as_time
    }

@gen.coroutine
def update5(attr, old, new):
    assigned_info = new.split(' ')[1:]
    
    for info in assigned_info:
        tmp = info.split(':')
        t = '_T'+str(tasks[tmp[0]])
        n = 'N'+str(node_short.index(tmp[1]))
        new_source6_df.loc[new_source6_df.nodes==n,'assigned_task']=new_source6_df.loc[new_source6_df.nodes==n,'assigned_task']+t
    source6.data = {
        'x' : new_source6_df.x,
        'y' : new_source6_df.y,
        'color':new_source6_df.color,
        'nodes':new_source6_df.nodes,
        'x_label':new_source6_df.x_label,
        'y_label':new_source6_df.y_label,
        'assigned_task':new_source6_df.assigned_task    
    }


###################################################################################################

global OUTFNAME, SERVER_IP, SUBSCRIPTIONS, DAG_PATH,NODE_PATH
OUTFNAME = 'demo_original.html'
SERVER_IP = "127.0.0.1"
SUBSCRIPTIONS = 'JUPITER'
DAG_PATH = 'configuration.txt'
NODE_PATH = 'nodes.txt'

global start_time, finish_time, total_time, offset, input_num
start_time =[]
finish_time =0
total_time =0
offset = 0
input_num = 0

global source, source1, source2, source3,source4,source5,source6, source5_df, doc, nodes, m, p,p1

source = ColumnDataSource(data=dict(top=[0], bottom=[0],left=[0],right=[0], color=["#9ecae1"],line_color=["black"], line_width=[2]))
source1 = ColumnDataSource(data=dict(x=[8], y=[3.5], time=[''],text_font_style=['bold']))
source2 = ColumnDataSource(data=dict(top=[5.15],bottom=[4.85],left=[3.3],right=[3.7],color=["#C2D2F9"]))


global nodes, num_nodes,MAX_X,MAX_Y,tasks
nodes = k8s_get_nodes(NODE_PATH)
num_nodes = len(nodes)
MAX_X = 10
MAX_Y = 12
tasks = retrieve_tasks(DAG_PATH)
num_tasks = len(tasks)

doc = curdoc()
doc.title = 'CIRCE Visualization'

m = mq(outfname=OUTFNAME,subs=SUBSCRIPTIONS,server = SERVER_IP,port=1883,timeout=60,looptimeout=1)

###################################################################################################################################
node_id = ['N'+str(i) for i in nodes.keys()]
print(node_id)
node_short = [i[0] for i in nodes.values()]
node_full = [i[1] for i in nodes.values()]

source4 = ColumnDataSource(dict(node_id=node_id,node_short=node_short,node_full=node_full))
columns = [TableColumn(field="node_id", title="Node ID"),TableColumn(field="node_short", title="Node Name"),TableColumn(field="node_full", title="Full Name")]
data_table = DataTable(source=source4, columns=columns, width=400, height=230,
                       selectable=True)

title1 = Div(text='Node Information',style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=400, height=20)

assignment = ['N/A']*len(tasks.keys())
assign_time = ['N/A']*len(tasks.keys())
task_id = ['T'+str(i) for i in tasks.values()]
source5 = ColumnDataSource(data=dict(task_id=task_id,task_names=list(tasks.keys()),assigned = assignment,as_time=assign_time))
columns2 = [TableColumn(field="task_id", title="Task ID"),TableColumn(field="task_names", title="Tasks Names"),TableColumn(field="assigned", title="Assigned Node"),TableColumn(field="as_time", title="Assigned Time")]
data_table2 = DataTable(source=source5, columns=columns2, width=400, height=230,
                       selectable=True,editable=True)
title2 = Div(text='Task Mapping Information',style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=400, height=20)
source5_df=source5.to_df()
new_source5_df=source5.to_df()
data_table2.on_change('source', lambda attr, old, new: update4())

###################################################################################################################################

points = set()
while len(points) < num_nodes:
    ix = np.random.randint(1, MAX_X)
    iy = np.random.randint(1, MAX_Y)
    points.add((ix,iy))
x = [i[0] for i in points]
y = [i[1] for i in points]
x_label = [i - 0.3 for i in x]
y_label = [i - 0.2 for i in y]
c = brewer["Spectral"][9]
color = list(repeatlist(c, num_nodes))
assigned_task=[""]*len(points)
p = figure(x_range=(0, MAX_X+1), y_range=(0, MAX_Y+1),plot_width=500, plot_height=600)
p.background_fill_color = "#EEEDED"
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.xaxis.axis_label = 'Digital Ocean Clusters'
p.xaxis.axis_label_text_font_size='20pt'


source6 = ColumnDataSource(data=dict(x=x,y=y,color=color,nodes=node_id,x_label=x_label,y_label=y_label,assigned_task=assigned_task))

lab = LabelSet(x='x_label', y='y_label',text='nodes',text_font_style='bold',text_color='black',source=source6)
p.add_layout(lab)
w = p.circle( x='x',y='y', radius=0.8, fill_color='color',line_color='color',source=source6)

p.add_tools(HoverTool(
    tooltips=[
        ("node_id","@nodes"),
        ("assigned_task","@assigned_task"),
    ]
))

source6_df = source6.to_df()
new_source6_df = source6.to_df()


###################################################################################################################################

home_input = []
global_input = []
start_times = []
end_times = []
exec_times = []
source7 = ColumnDataSource(dict(home_id=home_input,global_input=global_input,start_times=start_times,end_times=end_times,exec_times=exec_times))
columns = [TableColumn(field="home_id", title="Home ID"),TableColumn(field="global_input", title="Global Input Name"),TableColumn(field="start_times", title="Enter time"),TableColumn(field="end_times", title="Finish tme"),TableColumn(field="exec_times", title="Make span")]
data_table3 = DataTable(source=source7, columns=columns, width=600, height=580,selectable=True)

title3 = Div(text='Global Input Information',style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=600, height=20)


task_name = []
local_input = []
local_enter_times = []
local_exec_times = []
local_finish_times = []
local_elapse_times = []
local_duration_times = []
local_waiting_times = []

source8 = ColumnDataSource(dict(task_name=task_name,local_input=local_input,local_enter_times=local_enter_times,local_exec_times=local_exec_times,local_finish_times=local_finish_times,local_elapse_times=local_elapse_times,local_duration_times=local_duration_times,local_waiting_times=local_waiting_times))
columns = [TableColumn(field="task_name", title="Task name"),TableColumn(field="local_input", title="Local Input"),
            TableColumn(field="local_enter_times", title="Enter time"),TableColumn(field="local_exec_times", title="Exec time"),
            TableColumn(field="local_finish_times", title="Finish time"),TableColumn(field="local_elapse_times", title="Elapse time"),
            TableColumn(field="local_duration_times", title="Duration time"),TableColumn(field="local_waiting_times", title="Waiting time")]
data_table4 = DataTable(source=source7, columns=columns, width=900, height=580,selectable=True)

title4 = Div(text='Local Input Information',style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=600, height=20)

###################################################################################################################################

p1=figure(plot_width=600, plot_height=600)
p1.background_fill_color = "#EEEDED"
p1.xgrid.grid_line_color = None
p1.ygrid.grid_line_color = None
p1.xaxis.axis_label = 'Network Anomaly Detection Task Graph'
p1.xaxis.axis_label_text_font_size='20pt'


p1.add_layout(Label(x= 4.5, y=4.7, text="CIRCE", text_color="black", text_font_style='bold',text_font_size='38pt'))


p1.quad(top=[5.15, 4.15, 4.15, 4.15, 3.15, 3.15, 3.15, 3.15, 3.15, 3.15, 2.15,2.15,2.15,1.15], 
    bottom=[4.85, 3.85,3.85,3.85, 2.85,2.85,2.85,2.85,2.85,2.85, 1.85,1.85,1.85, 0.85], 
    left=[3.3,1.3,3.3,5.3, 0.8, 1.8, 2.8, 3.8,  4.8,5.8, 1.3,3.3,5.3,3.3], 
    right=[3.7,1.7,3.7,5.7, 1.2, 2.2, 3.2,  4.2,   5.2,  6.2,     1.7,3.7,5.7,3.7],
    color=["#C2D2F9","#5984E8","#5984E8","#5984E8","#9380F0","#1906BF","#9380F0","#1906BF","#9380F0","#1906BF","#084594","#084594","#084594","#33148E"])



#p1.ellipse(3.5, 5, size=40, color="#C2D2F9") #localpro
localpro = Label(x=2.3, y=4.9, text='localpro',text_color='black',background_fill_color='#C2D2F9', background_fill_alpha=0.5)
p1.add_layout(localpro)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=1.5, y_end=4.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=3.5, y_end=4.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=5.5, y_end=4.2))


#p1.ellipse(1.5, 4, size=40, color="#5984E8") #aggregate0
aggregare0 = Label(x=1, y=4.3, text='aggregate0',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
p1.add_layout(aggregare0)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=3.83, x_end=1, y_end=3.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=3.83, x_end=2, y_end=3.2))


#p1.ellipse(3.5, 4, size=40, color="#5984E8") #aggregate1
aggregate1 = Label(x=3.15, y=4.3, text='aggregate1',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
p1.add_layout(aggregate1)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=3.83, x_end=3, y_end=3.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=3.83, x_end=4, y_end=3.2))


#p1.ellipse(5.5, 4, size=40, color="#5984E8") #aggregate2
aggregate2 = Label(x=5, y=4.3, text='aggregate2',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
p1.add_layout(aggregate2)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=3.83, x_end=5, y_end=3.2))
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=3.83, x_end=6, y_end=3.2))


#p1.ellipse(1, 3, size=40, color="#9380F0") #simple_detector0
simple_detector0 = Label(x=0.7, y=3.35, text='simple_detector0',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
p1.add_layout(simple_detector0)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1, y_start=2.83, x_end=1.45, y_end=2.18))


#p1.ellipse(2, 3, size=40, color="#1906BF") #astute_detector0
astute_detector0 = Label(x=1.5, y=2.6, text='astute_detector0',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
p1.add_layout(astute_detector0)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=2, y_start=2.83, x_end=1.55, y_end=2.18))


#p1.ellipse(3, 3, size=40, color="#9380F0") #simple_detector1
simple_detector1 = Label(x=2.5, y=3.35, text='simple_detector1',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
p1.add_layout(simple_detector1)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3, y_start=2.83, x_end=3.45, y_end=2.18))


#p1.ellipse(4, 3, size=40, color="#1906BF") #astute_detector1
astute_detector1 = Label(x=3.5, y=2.6, text='astute detector1',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
p1.add_layout(astute_detector1)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=4, y_start=2.83, x_end=3.55, y_end=2.18))


#p1.ellipse(5, 3, size=40, color="#9380F0") #simple_detector2
simple_detector2 = Label(x=4.5, y=3.35, text='simple_detector2',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
p1.add_layout(simple_detector2)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5, y_start=2.83, x_end=5.45, y_end=2.18))


#p1.ellipse(6, 3, size=40, color="#1906BF") #astute_detector2
astute_detector2 = Label(x=5.5, y=2.6, text='astute_detector2',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
p1.add_layout(astute_detector2)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=6, y_start=2.83, x_end=5.55, y_end=2.18))


#p1.ellipse(1.5, 2, size=40, color="#084594") #fusion_center0
fusion_center0 = Label(x=1, y=1.6, text='fusion_center0',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
p1.add_layout(fusion_center0)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=1.83, x_end=3.3, y_end=1.18))


#p1.ellipse(3.5, 2, size=40, color='#084594') #fusion_center1
fusion_center1 = Label(x=3, y=1.6, text='fusion_center1',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
p1.add_layout(fusion_center1)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=1.83, x_end=3.5, y_end=1.18))


#p1.ellipse(5.5, 2, size=40, color='#084594') #fusion_center2
fusion_center2 = Label(x=5, y=1.6, text='fusion_center2',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
p1.add_layout(fusion_center2)
p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=1.83, x_end=3.7, y_end=1.18))


#p1.ellipse(3.5, 1, size=40, color="#33148E") #global_fusion
global_fusion = Label(x=2, y=0.9, text='global_fusion',text_color='black',background_fill_color='#33148E', background_fill_alpha=0.5)
p1.add_layout(global_fusion)

ellipse_source = p1.quad(top='top', bottom='bottom', left='left', right='right',color='color', source= source2)

###################################################################################################################################
p2 = layout([widgetbox(data_table,width=400,height=280),title1,widgetbox(data_table2,width=400,height=280),title2],sizing_mode='fixed',width=400,height=600)
layout = row(p2,p,p1)
doc.add_root(layout)

p3 = column(title3,widgetbox(data_table3))
p4 = column(title4,widgetbox(data_table4))
doc.add_root(row(p3,p4))
doc.add_periodic_callback(update, 50) 