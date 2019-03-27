import networkx as nx
from tornado import gen
from functools import partial
from bokeh.models import Button, NumeralTickFormatter
from bokeh.palettes import RdYlBu3
from bokeh.plotting import *
from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, Label, Arrow, NormalHead, LabelSet
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.io import output_file, show
from bokeh.layouts import row
import paho.mqtt.client as mqtt
import time
import numpy as np

DAG_PATH = 'configuration.txt'
NODE_PATH = 'nodes.txt'

MAX_X = 10
MAX_Y = 10



def gen_DAG(fname):
    """
    read input file from fname, return adj list.
    """
    adj_from_txt = dict()
    node_name_mapping = dict()   # mapping from node name to index
    with open(fname) as f:
        for i,line in enumerate(f):
            if i == 0:
                num_nodes = int(line.strip('\n'))
            else:
                node_list_txt = line.split()[0]
                node_name_mapping[node_list_txt] = i-1
    with open(fname) as f:
        for i,line in enumerate(f):
            if i == 0:
                continue
            if i == num_nodes:
                adj_from_txt[node_name_mapping[line.split()[0]]] = []
                continue
            node_idx = node_name_mapping[line.split()[0]]
            adj_from_txt[node_idx] = [node_name_mapping[nli] for nli in line.split()[3:]]
    return adj_from_txt, node_name_mapping

def k8s_get_nodes(node_info_file):
  """read the node info from the file input
  
  Args:
      node_info_file (str): path of ``node.txt``
  
  Returns:
      dict: node information 
  """
  nodes = {}
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      nodes.setdefault(node_line[0], [])
      for i in range(1, len(node_line)):
          nodes[node_line[0]].append(node_line[i])
  return nodes

def gen_node_cluster(node_file):
    nodes = k8s_get_nodes(node_file)
    num_nodes = len(nodes)
    x = np.random.randint(low=1, high=MAX_X, size=num_nodes)
    y = np.random.randint(low=1, high=MAX_Y, size=num_nodes)
    idx = np.arange(start= 1, stop=len(x))
    nodes = [str(i) for i in idx]
    # x_label = [item-0.3 for item in x]
    # y_label = [item+0.8 for item in y]
    source = ColumnDataSource(data=dict(x=x, y=y, nodes=nodes))
    # source = ColumnDataSource(data=dict(x=x, y=y, nodes=nodes,x_label=x_label,y_label=y_label))
    p = figure(x_range=(0, MAX_X+1), y_range=(0, MAX_Y+1), plot_width=400, plot_height=400)
    p.circle( x='x', y='y', radius=0.5, color='blue', source=source)
    lab = LabelSet(x='x', y='y',text_font_size="10pt", text='nodes',text_font_style='bold',text_color='black',source=source)
    p.add_layout(lab)
    return p




def generate_nx_graph(adj_list):
    """
    construct a graph of networkx type.
    We want networkx type in order to get the layout, since networkx
    integrated the graphviz layout library for DAG graphs.
    """
    G = nx.DiGraph()
    for node in adj_list.keys():
        G.add_node(node)
        G.add_edges_from([(node,u) for u in adj_list[node]])
    return G


doc = curdoc()
doc.title = 'Test'

adj_from_txt, node_name_mapping = gen_DAG(DAG_PATH)
print(adj_from_txt)
print(node_name_mapping)

G = generate_nx_graph(adj_from_txt)

# print(G)
p = gen_node_cluster(NODE_PATH)

doc.add_root(p)