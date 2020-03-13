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
import os


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


global OUTFNAME, SERVER_IP, DAG_PATH, EXP,folder
OUTFNAME = 'users_management.html'
SERVER_IP = "127.0.0.1"
DAG_PATH = '../app_specific_files/dummy_app_100/configuration.txt'
EXP = 'Experiment 1'
folder = 'exp1'
EXP = 'Experiment 1'


global tasks,taskid,userid,usertask
tasks,tasksid = retrieve_tasks(DAG_PATH)


global doc, data_table,source
N = len(tasks)
M = 5
cid = 1
userid = []
usertask = []
for i in range(1,N+1):
    cur_task = tasksid[i]
    for j in range(0,M):
        user_id = 'U'+str(cid)
        cur_sub = cur_task
        userid.append(user_id)
        usertask.append(cur_task)
        cid = cid+1

source = ColumnDataSource(dict(user_id=userid,topics=usertask))
columns = [TableColumn(field="user_id", title="User ID"),TableColumn(field="topics", title="Topics")]
data_table = DataTable(source=source, columns=columns, width=1000, height=1000,selectable=True)
ti = '%s - Subscriber Information'%(EXP)
title1 = Div(text=ti,style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=400, height=20)

doc = curdoc()
doc.title = 'Users management'
p1 = layout([title1,widgetbox(data_table,width=1000,height=1000)])
layout = row(p1)
doc.add_root(layout) 


