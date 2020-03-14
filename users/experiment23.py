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


def get_app_list(app_path_list):
    app_option = []
    dir_list = next(os.walk(app_path_list))[1]
    for d in dir_list:
        app_option.append(d)

    return app_option


global OUTFNAME, SERVER_IP, DAG_PATH, EXP,folder
OUTFNAME = 'users_management.html'
SERVER_IP = "127.0.0.1"
APP_PATH_LIST = '../app_specific_files/dummy_app_combined/dummy_app_list'
EXP = 'Experiment 3'
folder = 'exp3'
EXP = 'Experiment 3'


global userid,userapp,app_options
app_options = get_app_list(APP_PATH_LIST)

print(app_options)

N = len(app_options)
M = 5 #exp3
cid = 1
userid = []
userapp = []

for i in range(1,N+1):
    cur_app = 'dummyapp%d'%(i)
    for j in range(0,M):
        user_path = '%s/user%d'%(folder,cid)
        user_log = '%s/user%d/user%d.log'%(folder,cid,cid)
        user_id = 'U'+str(cid)
        cur_sub = cur_app
        userid.append(user_id)
        userapp.append(cur_app)
        cid = cid+1

global doc, data_table,source
source = ColumnDataSource(dict(user_id=userid,topics=userapp))
columns = [TableColumn(field="user_id", title="User ID"),TableColumn(field="topics", title="Topics")]
data_table = DataTable(source=source, columns=columns, width=1000, height=1000,selectable=True)
ti = '%s - Subscriber Information'%(EXP)
title1 = Div(text=ti,style={'font-size': '15pt', 'color': 'black','text-align': 'center'},width=400, height=20)

doc = curdoc()
doc.title = 'Users management'
p1 = layout([title1,widgetbox(data_table,width=1000,height=1000)])
layout = row(p1)
doc.add_root(layout)

