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

def get_dag_nodes(lines):
    nodes = []
    for line in lines:
        nodes.append(line.rstrip().split(" ")[0])
    return nodes

def get_dag_links(lines):
    links = []
    for i, line in enumerate(lines):
        arr = line.rstrip().split(" ")
        node = arr[0]
        print(arr)
        if i < len(lines)-1:
            for i, each in enumerate(arr):
                if i >= 3:
                    links.append((node, arr[i].replace("\n","")))
    return links

class mq():


    def __init__(self,outfname,subs,server,port,timeout,looptimeout,nodes):
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
        self.nodes = nodes
        self.start_messages = [x+' starts' for x in self.nodes]
        self.end_messages = [x+' ends' for x in self.nodes]

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self,client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        subres = client.subscribe(self.subs,qos=1)
        print("Connected with result code "+str(rc))


    # The callback for when a PUBLISH message is received from the server.
    def on_message(self,client, userdata, msg):
        
        
        print(self.start_messages)
        print(self.end_messages)


        top_dag=[5.15, 4.15, 4.15, 4.15, 3.15, 3.15, 3.15, 3.15, 3.15, 3.15, 2.15,2.15,2.15,1.15]
        bottom_dag=[4.85, 3.85,3.85,3.85, 2.85,2.85,2.85,2.85,2.85,2.85, 1.85,1.85,1.85, 0.85]
        left_dag= [3.3,1.3,3.3,5.3, 0.8, 1.8, 2.8, 3.8, 4.8,5.8, 1.3,3.3,5.3,3.3]
        right_dag=[3.7,1.7,3.7,5.7, 1.2, 2.2, 3.2, 4.2, 5.2, 6.2,1.7,3.7,5.7,3.7]


        message = msg.payload.decode()
        global start_time
        global finish_time
        global total_time

        print('--------------')
        print(message)
        print('--------------')
        if message in start_messages:
            index = start_messages.index(message)
            topd,bottomd,leftd,rightd = top_dag[index],bottom_dag[index],left_dag[index],right_dag[index]
            color = "red"
            doc.add_next_tick_callback(partial(update3, top= topd, bottom=bottomd,left=leftd,right=rightd, color=color))
            

        elif message in end_messages:

            index = end_messages.index(message)
            topd,bottomd,leftd,rightd = top_dag[index],bottom_dag[index],left_dag[index],right_dag[index]


            color=['#C2D2F9',"#5984E8","#5984E8","#5984E8","#9380F0","#9380F0","#9380F0",
            "#1906BF","#1906BF","#1906BF", '#084594','#084594','#084594',"#33148E"]
            color1=["#C2D2F9","#5984E8","#5984E8","#5984E8","#9380F0","#1906BF","#9380F0",
            "#1906BF","#9380F0","#1906BF","#084594","#084594","#084594","#33148E"]

            doc.add_next_tick_callback(partial(update3, top= topd, bottom=bottomd,left=leftd,right=rightd, color=color1[index]))

        elif message.startswith('mapping'):
            print('---- Receive task mapping')
            doc.add_next_tick_callback(partial(update5,new=message,old=source6_df,attr=source6.data))
            doc.add_next_tick_callback(partial(update4,new=message,old=source5_df,attr=data_table2.source))
        elif message.startswith('runtime'):
            print('---- Receive runtime statistics')
            doc.add_next_tick_callback(partial(update8,new=message,old=source8_df,attr=data_table4.source))
        elif message.startswith('global'):
            print('-----Receive global information')
            doc.add_next_tick_callback(partial(update7,new=message,old=source7_df,attr=data_table3.source))




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
        new_source5_df.loc[new_source5_df.task_names==tmp[0],'as_time']=convert_time(tmp[2])

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

@gen.coroutine
def update7(attr, old, new):

    tmp = new.split(' ')[1:]
    home_id = tmp[0]
    if tmp[1]=='start':
        data = ['N/A','N/A',tmp[2],tmp[0],convert_time(tmp[3])]
        new_source7_df.loc[len(new_source7_df),:]=data
    else:
        new_source7_df.loc[(new_source7_df.home_id==tmp[0]) & (new_source7_df.global_input==tmp[2]),'end_times']=convert_time(tmp[3])
        tmp1 = new_source7_df.loc[(new_source7_df.home_id==tmp[0]) & (new_source7_df.global_input==tmp[2]),'end_times']
        tmp2 = new_source7_df.loc[(new_source7_df.home_id==tmp[0]) & (new_source7_df.global_input==tmp[2]),'start_times'] 
        new_source7_df.loc[(new_source7_df.home_id==tmp[0]) & (new_source7_df.global_input==tmp[2]),'exec_times']=time_delta(tmp1,tmp2)
    source7.data = {
        'home_id'       : new_source7_df.home_id,
        'global_input'  : new_source7_df.global_input,
        'start_times'   : new_source7_df.start_times,
        'end_times'     : new_source7_df.end_times,
        'exec_times'    : new_source7_df.exec_times,
    }

@gen.coroutine
def update8(attr, old, new):
    tmp = new.split(' ')[1:]
    if tmp[0]=='enter':
        data = ['N/A','N/A',convert_time(tmp[3]),'N/A','N/A',tmp[2],'N/A',tmp[1]]
        new_source8_df.loc[len(new_source8_df),:]=data    
    elif tmp[0]=='exec':
        new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_exec_times']=convert_time(tmp[3])
        tmp1 = new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_exec_times']
        tmp2 = new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_enter_times']
        new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_waiting_times']=time_delta(tmp1,tmp2)    
    else:
        new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_finish_times']=convert_time(tmp[3])
        tmp1 = new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_finish_times']
        tmp2 = new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_enter_times']
        tmp3 = new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_exec_times']
        new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_elapse_times']=time_delta(tmp1,tmp2)   
        new_source8_df.loc[(new_source8_df.task_name==tmp[1]) & (new_source8_df.local_input==tmp[2]),'local_duration_times']=time_delta(tmp1,tmp3) 

    source8.data = {
        'local_duration_times'  : new_source8_df.local_duration_times,
        'local_elapse_times'    : new_source8_df.local_elapse_times,
        'local_enter_times'     : new_source8_df.local_enter_times,
        'local_exec_times'      : new_source8_df.local_exec_times,
        'local_finish_times'    : new_source8_df.local_finish_times,
        'local_input'           : new_source8_df.local_input,
        'local_waiting_times'   : new_source8_df.local_waiting_times,
        'task_name'             : new_source8_df.task_name
    }




def convert_time(t):
    return datetime.datetime.fromtimestamp(float(t)).strftime("%d.%m.%y %H:%M:%S")
def time_delta(end,start): 
    tmp1 = datetime.datetime.strptime(end.iloc[0],"%d.%m.%y %H:%M:%S")
    tmp2 = datetime.datetime.strptime(start.iloc[0],"%d.%m.%y %H:%M:%S")
    delta = (tmp1-tmp2).total_seconds()
    return delta

###################################################################################################

global OUTFNAME, SERVER_IP, SUBSCRIPTIONS, DAG_PATH,NODE_PATH
OUTFNAME = 'demo_original.html'
SERVER_IP = "127.0.0.1"
SUBSCRIPTIONS = 'JUPITER'
DAG_PATH = '../app_specific_files/dummy_app/configuration.txt'
NODE_PATH = '../nodes.txt'

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

m = mq(outfname=OUTFNAME,subs=SUBSCRIPTIONS,server = SERVER_IP,port=1883,timeout=60,looptimeout=1,nodes=tasks)

###################################################################################################################################

global data_table, data_table2, source5_df,new_source5_df,source6_df,new_source6_df

node_id = ['N'+str(i) for i in nodes.keys()]
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

global data_table3, data_table4, source7_df,new_source7_df,source8_df,new_source8_df

home_id = []
global_input = []
start_times = []
end_times = []
exec_times = []
source7 = ColumnDataSource(dict(home_id=home_id,global_input=global_input,start_times=start_times,end_times=end_times,exec_times=exec_times))
columns = [TableColumn(field="home_id", title="Home ID"),TableColumn(field="global_input", title="Global Input Name"),TableColumn(field="start_times", title="Enter time"),TableColumn(field="end_times", title="Finish tme"),TableColumn(field="exec_times", title="Make span [s]")]
data_table3 = DataTable(source=source7, columns=columns, width=600, height=580,selectable=True)

title3 = Div(text='Global Input Information',style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=600, height=20)

source7_df=source7.to_df()
new_source7_df=source7.to_df()
data_table3.on_change('source', lambda attr, old, new: update7())

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
data_table4 = DataTable(source=source8, columns=columns, width=900, height=580,selectable=True)

title4 = Div(text='Local Input Information',style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=600, height=20)

source8_df=source8.to_df()
new_source8_df=source8.to_df()
data_table4.on_change('source', lambda attr, old, new: update8())


file = open(DAG_PATH, 'r')
lines = file.readlines()
lines.pop(0)
nodes = get_dag_nodes(lines)
links = get_dag_links(lines)

G = nx.DiGraph()
G.add_nodes_from(nodes)
G.add_edges_from(links)
pos = graphviz_layout(G ,prog='dot')

# calculate the range for task graph
range_x = [0,0]
range_y = [0,0]
for each in pos.values():
    range_x[0] = min(range_x[0], int(each[0]))
    range_x[1] = max(range_x[1], int(each[0]))
    range_y[0] = min(range_y[0], int(each[1]))
    range_y[1] = max(range_y[1], int(each[1]))
range_x = [range_x[0]-50, range_x[1]+150]
range_y = [range_y[0]-50, range_y[1]+50]

p1 = Plot(plot_width=700, plot_height=700,
    x_range=Range1d(range_x[0], range_x[1]), y_range=Range1d(range_y[0], range_y[1]))
p1.title.text = "DAG"
p.title.text_font_size = '20pt'
node_hover_tool = HoverTool(tooltips=[("task", "@index")])
p1.add_tools(node_hover_tool, BoxZoomTool(), ResetTool())


global graph
graph = from_networkx(G, pos, scale=1, center=(0,0))


colors = []
indexs = []
for i,each in enumerate(nodes):
    indexs.append(i)
    colors.append('blue')
graph.node_renderer.data_source.data['colors'] = colors
graph.node_renderer.data_source.data['name'] = nodes

graph.node_renderer.glyph = Circle(size=15, fill_color='colors')
graph.edge_renderer.glyph = MultiLine(line_color="black", line_alpha=0.8, line_width=1)
p1.renderers.append(graph)

# code = """
#     var result = new Float64Array(xs.length)
#     for (var i = 0; i < xs.length; i++) {
#         result[i] = provider.graph_layout[xs[i]][%s]
#     }
#     return result
# """
# xcoord = CustomJSTransform(v_func=code % "0", args=dict(provider=graph.layout_provider))
# ycoord = CustomJSTransform(v_func=code % "1", args=dict(provider=graph.layout_provider))

# # Use the transforms to supply coords to a LabelSet 
# labels = LabelSet(x=transform('index', xcoord),
#                   y=transform('index', ycoord),
#                   text='names', text_font_size="12px",
#                   x_offset=5, y_offset=5,
#                   source=source, render_mode='canvas')
# p1.renderers.append(labels)

# add labels to each node
# x, y = zip(*graph.layout_provider.graph_layout.values())
# node_labels = nx.get_node_attributes(G, 'name')
# #node_labels = graph.node_renderer.data_source.data['name']
# print(node_labels)
# print(graph.node_renderer.data_source.data['name'])

# source = ColumnDataSource({'x': x, 'y': y,
#                            'task': tuple(node_labels)})

# labels = LabelSet(x='x', y='y', text='task', source=source,
#                   background_fill_color='white', x_offset=(-30), y_offset=8,
#                   text_font_size="9pt")
# p1.renderers.append(labels)

# p1=figure(plot_width=600, plot_height=600)
# p1.background_fill_color = "#EEEDED"
# p1.xgrid.grid_line_color = None
# p1.ygrid.grid_line_color = None
# p1.xaxis.axis_label = 'Network Anomaly Detection Task Graph'
# p1.xaxis.axis_label_text_font_size='20pt'


# p1.add_layout(Label(x= 4.5, y=4.7, text="JUPITER", text_color="black", text_font_style='bold',text_font_size='32pt'))


# p1.quad(top=[5.15, 4.15, 4.15, 4.15, 3.15, 3.15, 3.15, 3.15, 3.15, 3.15, 2.15,2.15,2.15,1.15], 
#     bottom=[4.85, 3.85,3.85,3.85, 2.85,2.85,2.85,2.85,2.85,2.85, 1.85,1.85,1.85, 0.85], 
#     left=[3.3,1.3,3.3,5.3, 0.8, 1.8, 2.8, 3.8,  4.8,5.8, 1.3,3.3,5.3,3.3], 
#     right=[3.7,1.7,3.7,5.7, 1.2, 2.2, 3.2,  4.2,   5.2,  6.2,     1.7,3.7,5.7,3.7],
#     color=["#C2D2F9","#5984E8","#5984E8","#5984E8","#9380F0","#1906BF","#9380F0","#1906BF","#9380F0","#1906BF","#084594","#084594","#084594","#33148E"])



# #p1.ellipse(3.5, 5, size=40, color="#C2D2F9") #localpro
# localpro = Label(x=2.3, y=4.9, text='localpro',text_color='black',background_fill_color='#C2D2F9', background_fill_alpha=0.5)
# p1.add_layout(localpro)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=1.5, y_end=4.2))
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=3.5, y_end=4.2))
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=4.85, x_end=5.5, y_end=4.2))


# #p1.ellipse(1.5, 4, size=40, color="#5984E8") #aggregate0
# aggregare0 = Label(x=1, y=4.3, text='aggregate0',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
# p1.add_layout(aggregare0)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=3.83, x_end=1, y_end=3.2))
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=3.83, x_end=2, y_end=3.2))


# #p1.ellipse(3.5, 4, size=40, color="#5984E8") #aggregate1
# aggregate1 = Label(x=3.15, y=4.3, text='aggregate1',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
# p1.add_layout(aggregate1)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=3.83, x_end=3, y_end=3.2))
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=3.83, x_end=4, y_end=3.2))


# #p1.ellipse(5.5, 4, size=40, color="#5984E8") #aggregate2
# aggregate2 = Label(x=5, y=4.3, text='aggregate2',text_color='black',background_fill_color='#5984E8', background_fill_alpha=0.5)
# p1.add_layout(aggregate2)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=3.83, x_end=5, y_end=3.2))
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=3.83, x_end=6, y_end=3.2))


# #p1.ellipse(1, 3, size=40, color="#9380F0") #simple_detector0
# simple_detector0 = Label(x=0.7, y=3.35, text='simple_detector0',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
# p1.add_layout(simple_detector0)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1, y_start=2.83, x_end=1.45, y_end=2.18))


# #p1.ellipse(2, 3, size=40, color="#1906BF") #astute_detector0
# astute_detector0 = Label(x=1.5, y=2.6, text='astute_detector0',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
# p1.add_layout(astute_detector0)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=2, y_start=2.83, x_end=1.55, y_end=2.18))


# #p1.ellipse(3, 3, size=40, color="#9380F0") #simple_detector1
# simple_detector1 = Label(x=2.5, y=3.35, text='simple_detector1',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
# p1.add_layout(simple_detector1)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3, y_start=2.83, x_end=3.45, y_end=2.18))


# #p1.ellipse(4, 3, size=40, color="#1906BF") #astute_detector1
# astute_detector1 = Label(x=3.5, y=2.6, text='astute detector1',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
# p1.add_layout(astute_detector1)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=4, y_start=2.83, x_end=3.55, y_end=2.18))


# #p1.ellipse(5, 3, size=40, color="#9380F0") #simple_detector2
# simple_detector2 = Label(x=4.5, y=3.35, text='simple_detector2',text_color='black',background_fill_color='#9380F0', background_fill_alpha=0.5)
# p1.add_layout(simple_detector2)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5, y_start=2.83, x_end=5.45, y_end=2.18))


# #p1.ellipse(6, 3, size=40, color="#1906BF") #astute_detector2
# astute_detector2 = Label(x=5.5, y=2.6, text='astute_detector2',text_color='black',background_fill_color='#1906BF', background_fill_alpha=0.7)
# p1.add_layout(astute_detector2)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=6, y_start=2.83, x_end=5.55, y_end=2.18))


# #p1.ellipse(1.5, 2, size=40, color="#084594") #fusion_center0
# fusion_center0 = Label(x=1, y=1.6, text='fusion_center0',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
# p1.add_layout(fusion_center0)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=1.5, y_start=1.83, x_end=3.3, y_end=1.18))


# #p1.ellipse(3.5, 2, size=40, color='#084594') #fusion_center1
# fusion_center1 = Label(x=3, y=1.6, text='fusion_center1',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
# p1.add_layout(fusion_center1)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=3.5, y_start=1.83, x_end=3.5, y_end=1.18))


# #p1.ellipse(5.5, 2, size=40, color='#084594') #fusion_center2
# fusion_center2 = Label(x=5, y=1.6, text='fusion_center2',text_color='black',background_fill_color='#084594', background_fill_alpha=0.5)
# p1.add_layout(fusion_center2)
# p1.add_layout(Arrow(end=NormalHead(line_color="black", line_width=1, size=10),x_start=5.5, y_start=1.83, x_end=3.7, y_end=1.18))


# #p1.ellipse(3.5, 1, size=40, color="#33148E") #global_fusion
# global_fusion = Label(x=2, y=0.9, text='global_fusion',text_color='black',background_fill_color='#33148E', background_fill_alpha=0.5)
# p1.add_layout(global_fusion)

# ellipse_source = p1.quad(top='top', bottom='bottom', left='left', right='right',color='color', source= source2)

###################################################################################################################################
p2 = layout([title1,widgetbox(data_table,width=400,height=280),title2,widgetbox(data_table2,width=400,height=280)],sizing_mode='fixed',width=400,height=600)
layout = row(p2,p,p1)
doc.add_root(layout)

p3 = column(title3,widgetbox(data_table3))
p4 = column(title4,widgetbox(data_table4))
doc.add_root(row(p3,p4))
doc.add_periodic_callback(update, 50) 