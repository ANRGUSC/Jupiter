import sys
import jupiter_config
import time
import os
from os import path
from multiprocessing import Process
# from readconfig import k8s_read_config, read_config
from k8s_profiler_scheduler import *
from k8s_wave_scheduler import *
from k8s_circe_scheduler import *
from delete_all_circe_deployments import *
from delete_all_profilers import *
from delete_all_waves import *
from pprint import *
import jupiter_config
import requests
import json
from pprint import *

"""
  read the dag from the file input
"""
def k8s_read_dag(dag_info_file):

  dag_info=[]
  config_file = open(dag_info_file,'r')
  dag_size = int(config_file.readline())

  dag={}
  for i, line in enumerate(config_file, 1):
      dag_line = line.strip().split(" ")
      if i == 1:
          dag_info.append(dag_line[0])
      dag.setdefault(dag_line[0], [])
      for j in range(1,len(dag_line)):
          dag[dag_line[0]].append(dag_line[j])
      if i == dag_size:
          break

  dag_info.append(dag)
  return dag_info


def k8s_get_nodes(node_info_file):

  nodes = {}
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      nodes.setdefault(node_line[0], [])
      for i in range(1, len(node_line)):
          nodes[node_line[0]].append(node_line[i])
  return nodes
    

def k8s_get_hosts(dag_info_file, node_info_file, mapping):

  dag_info = k8s_read_dag(dag_info_file)
  nodes = k8s_get_nodes(node_info_file)
  print(nodes)
  hosts={}

  for i in mapping:
      #get task, node IP, username and password
      print(i, mapping[i], nodes[mapping[i]])
      hosts.setdefault(i,[])
      hosts[i].append(i)                          # task
      hosts[i].extend(nodes[mapping[i]])      # assigned node id
      
  hosts.setdefault('home',[])
  hosts['home'].append('home')
  hosts['home'].extend(nodes.get('home'))
  dag_info.append(hosts)
  return dag_info
