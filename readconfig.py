"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import os

def k8s_read_config(path1):

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
        hosts.setdefault(myline[0],[])
        hosts[myline[0]].append(myline[1])

    hosts.setdefault('home',[])
    hosts['home'].append('home')

    dag_info.append(hosts)
    return dag_info

def read_config(path1,path2):

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

    nodes = {}
    node_file = open(path2, "r")
    for line in node_file:
        node_line = line.strip().split(" ")
        nodes.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
            nodes[node_line[0]].append(node_line[i])
    return nodes
    

