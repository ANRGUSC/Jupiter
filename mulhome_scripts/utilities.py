"""
   This script contains all useful functions to be used in the system, for example, reading input files.
"""
__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
import time
import os
from os import path
from pprint import *


def k8s_read_config(configuration_file):
    """read the configuration  from ``configuration.txt`` file
    
    Args:
        configuration_file (str): path of ``configuration.txt``
    
    Returns:
        dict: DAG information 
    """
    dag_info=[]
    config_file = open(configuration_file,'r')
    dag_size = int(config_file.readline())

    dag={}
    for i, line in enumerate(config_file, 1):
        dag_line = line.strip().split(" ")
        if i == 1:
            dag_info.append(dag_line[0])
        dag.setdefault(dag_line[0], [])
        for j in range(1,len(dag_line)):
            dag[dag_line[0]].append(dag_line[j])
        if i==dag_size:
            break

    dag_info.append(dag)

    hosts={}
    for line in config_file:
        #get task, node IP, username and password
        myline = line.strip().split(" ")
        hosts.setdefault(myline[0],[])
        hosts[myline[0]].append(myline[1])

    hosts.setdefault('home',[])
    hosts['home'].append('home')

    dag_info.append(hosts)
    return dag_info


# Old k8s_read_dag - No home and datasources support
def k8s_read_dag(dag_info_file):
  """read the dag from the file input
  
  Args:
      dag_info_file (str): path of DAG file
  
  Returns:
      dict: DAG information 
  """
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

# Support home and datasources
# def k8s_read_dag(dag_info_file):
#   """read the dag from the file input
  
#   Args:
#       dag_info_file (str): path of DAG file
  
#   Returns:
#       dict: DAG information 
#   """
#   dag_info=[]
#   config_file = open(dag_info_file,'r')
#   dag_size = int(config_file.readline())

#   dag={}
#   c = 0
#   for i, line in enumerate(config_file, 1):
#       dag_line = line.strip().split(" ")
#       # if i == 1:
#       #     dag_info.append(dag_line[0])
#       if (dag_line[0].startswith('home') | dag_line[0].startswith('datasource')): 
#         dag_info.append(dag_line[0]
          
#       dag.setdefault(dag_line[0], [])
#       for j in range(1,len(dag_line)):
#           dag[dag_line[0]].append(dag_line[j])
#       if i == dag_size:
#           break

#   dag_info.append(dag)
#   return dag_info

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

def k8s_get_nodes_worker(node_info_file):
  """read the node info (only workers) and home workers from the file input
  
  Args:
      node_info_file (str): path of ``node.txt``
  
  Returns:
      dict: node information 
  """
  nodes = {}
  homes = {}
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      if node_line[0].startswith('home'): 
        homes.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
          homes[node_line[0]].append(node_line[i])
        continue
      nodes.setdefault(node_line[0], [])
      for i in range(1, len(node_line)):
          nodes[node_line[0]].append(node_line[i])
  #print(nodes)
  return nodes, homes

def k8s_get_all_elements(node_info_file):
  """read the node info from the file input
  
  Args:
      node_info_file (str): path of ``node.txt``
  
  Returns:
      dict: node information 
  """
  nodes = {}
  homes = {}
  datasources = {}
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      if node_line[0].startswith('home'): 
        homes.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
          homes[node_line[0]].append(node_line[i])
      elif node_line[0].startswith('datasource'):
        datasources.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
          datasources[node_line[0]].append(node_line[i])
      else:
        nodes.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
            nodes[node_line[0]].append(node_line[i])
  return nodes, homes,datasources

    
  

def k8s_get_hosts(dag_info_file, node_info_file, mapping):
  """read the hosts info from the input files
  
  Args:
      - dag_info_file (str): path of ``configuration.txt``
      - node_info_file (str): path of ``node.txt``  
      - mapping (dict): mapping between task and assigned node 
  
  Returns:
      dict: DAG information and its corresponding mapping
  """

  dag_info = k8s_read_dag(dag_info_file)
  nodes = k8s_get_nodes(node_info_file)
  print(nodes)
  hosts={}

  print('Receive mapping')
  print(mapping)
  """
  example mapping
  {'task0': ['node1', 0.167513777340025, 'node3', 0.4223052081895984, 'node5', 0.41018101447037664], 
   'task1': ['node2', 0.7338789970245765, 'node7', 0.2661210029754235], 
   'task2': 'node6', 
   'task3': 'node4'}
  """
  for i in mapping:
      if  type(mapping[i]) is list:
          for index in range(len(mapping[i])):
              if index % 2 == 0:
                  #get task, node IP, username and password
                  print(i, mapping[i][index], nodes[mapping[i][index]])
                  hosts.setdefault(i,[])
                  hosts[i].append(i)                          # task
                  hosts[i].extend(nodes[mapping[i][index]])      # assigned node id
      else:
          #get task, node IP, username and password
          print(i, mapping[i], nodes[mapping[i]])
          hosts.setdefault(i,[])
          hosts[i].append(i)                          # task
          hosts[i].extend(nodes[mapping[i]])      # assigned node id
      
  hosts.setdefault('home',[])
  hosts['home'].append('home')
  hosts['home'].extend(nodes.get('home'))
  dag_info.append(hosts)
  dag_info.append(nodes)
  """
  example return
  ['task0',
   {'task0': ['1', 'true', 'task1', 'task2'],
    'task1': ['1', 'true', 'task3'],
    'task2': ['1', 'true', 'task3'],
    'task3': ['2', 'true', 'home']},
   {'home': ['home', 'ubuntu-s-2vcpu-4gb-sfo2-01'],
    'task0': ['task0', 'ubuntu-s-1vcpu-2gb-nyc3-02'],
    'task1': ['task1', 'ubuntu-s-1vcpu-2gb-nyc3-01'],
    'task2': ['task2', 'ubuntu-s-1vcpu-2gb-nyc3-01'],
    'task3': ['task3', 'ubuntu-s-1vcpu-2gb-nyc3-01']}
    {NODES}
  ]
  """
  return dag_info


def k8s_get_nodes_string(node_info_file):
  """read the node info from the file input
  
  Args:
      node_info_file (str): path of ``node.txt``
  
  Returns:
      str: node information in string format
  """
  nodes = ""
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      if node_line[0].startswith("home"):
        continue
      nodes = nodes + ":" + str(node_line[0])
  return nodes

def k8s_get_nodes_homes_string(node_info_file):
  """read the node info and the home info from the file input
  
  Args:
      node_info_file (str): path of ``node.txt``
  
  Returns:
      str: node information/ home information in string format
  """
  nodes = ""
  homes = ""
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      if node_line[0].startwith("home"):
        homes = homes + ":" + str(node_line[0])
      nodes = nodes + ":" + str(node_line[0])
  return nodes,homes

if __name__ == '__main__':
  dag_info_file = '../app_specific_files/dummy_datasources/configuration.txt'
  dag_info = k8s_read_dag(dag_info_file)
  
