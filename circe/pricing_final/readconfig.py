__author__ = "Aleksandra Knezevic,Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar, Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import os

def read_config(path1,path2):
    """
    Reads ``configuration.txt`` and ``nodes.txt``

    Args:
        - path1 (str): the path to ``configuration.txt``
        - path2 (str): the path to ``nodes.txt``

    Returns:
        dict: DAG info (task-node mapping, child tasks and node information)

    """
    
    nodes = {}
    node_file = open(path2, "r")
    for line in node_file:
        node_line = line.strip().split(" ")
        nodes.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
            nodes[node_line[0]].append(node_line[i])

    dag_info=[]
    config_file = open(path1,'r')
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
        print(myline)
        hosts.setdefault(myline[0],[])
        for j in range(0,2):
            if j==0:
                hosts[myline[0]].append(myline[j])
            if j==1:
                hosts[myline[0]].append(nodes.get(myline[1])[0])
                hosts[myline[0]].append(nodes.get(myline[1])[1])
                hosts[myline[0]].append(nodes.get(myline[1])[2])

    hosts.setdefault('home',[])
    hosts['home'].append('home')
    hosts['home'].append(nodes.get('home')[0])
    hosts['home'].append(nodes.get('home')[1])
    hosts['home'].append(nodes.get('home')[2])

    dag_info.append(hosts)
    return dag_info


def read_node_list(path2):
    """
    Reads ``nodes.txt``

    Args:
        path2 (str): the path to nodes.txt

    Returns:
        dict: nodes info

    """
    nodes = {}
    node_file = open(path2, "r")
    for line in node_file:
        node_line = line.strip().split(" ")
        nodes.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
            nodes[node_line[0]].append(node_line[i])
    return nodes
    

