"""
This code uses the output DAG of ``rand_task_gen.py``(by Diyi), which is used to generate a random DAG, to generate the corresponding dummy application working for Jupiter (version 3) , 

"""
__author__ = "Quynh Nguyen, Jiatong Wang, Diyi Hu and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "1.0"


import argparse
import numpy as np
import random
from functools import reduce
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import pylab as plt
import yaml
import os
import json
import shutil
from collections import defaultdict
from distutils.dir_util import copy_tree
import logging


EPSILON = 1e-2

def parse_args():
    parser = argparse.ArgumentParser(description='generate random task graphs')
    parser.add_argument("--conf",required=True,type=str,help='yaml file specifying task_dag generation parameters')
    return parser.parse_args()

def random_list(depth,total_num,width_min,width_max):
    list_t = []
    if total_num>= (depth-2)*width_min+2 and total_num<=(depth-2)*width_max+2:
        list_t.append(1)
        for i in range(depth-2):
            list_t.append(2)
        list_t.append(1)
        for i in range(total_num-sum(list_t)+2):
            while True:
                tmp = random.randint(1,len(list_t)-2)
                if list_t[tmp]+1 > 4:
                    pass
                else:
                    list_t[tmp] = list_t[tmp] + 1
                    break
    else:
        list_t.append(1)
        while True:
            t = random.randint(width_min,width_max)
            a = sum(list_t)-1+t
            b = total_num -(sum(list_t)-1)
            if (sum(list_t)-1+t)<total_num:
                list_t.append(t)
            elif  total_num -(sum(list_t)-1) >=width_min and total_num -(sum(list_t)-1)<=width_max :
                list_t.append(total_num -(sum(list_t)-1))
                break
            else:
                print('something wrong')
                pass
        list_t.append(1)
    return list_t

def gen_task_nodes(depth,total_num,width_min,width_max):
    #num_levels = depth+2       # 2: 1 for entry task, 1 for exit task
    if depth==1:
        num_list = [1,total_num,1]
    else:
        num_list = random_list(depth+2,total_num,width_min,width_max)
    num_levels = len(num_list)
    num_nodes_per_level = np.array(num_list)
    #num_nodes_per_level = np.array([random.randint(width_min,width_max) for i in range(num_levels)])
    num_nodes_per_level[0] = 1.
    num_nodes_per_level[-1] = 1.
    num_nodes = num_nodes_per_level.sum()
    level_per_task = reduce(lambda a,b:a+b, [[enum]*val for enum,val in enumerate(num_nodes_per_level)],[])
    #e.g. [0,1,2,2,3,3,3,3,4]
    level_per_task = {i:level_per_task[i] for i in range(num_nodes)}
    #level_per_task in the format of {task_i: level_of_i}
    task_per_level = {i:[] for i in range(num_levels)}
    for ti,li in level_per_task.items():
        task_per_level[li] += [ti]
        # task_per_level in the format of {level_i:[tasks_in_level_i]}
    return task_per_level, level_per_task

def gen_task_links(deg_mu,deg_sigma,task_per_level,level_per_task,delta_lvl=2):
    num_tasks = len(level_per_task)
    num_level = len(task_per_level)
    neighs_top_down = {t:np.array([]) for t in range(num_tasks)}
    neighs_down_top = {t:np.array([]) for t in range(num_tasks)}
    deg = np.random.normal(deg_mu,deg_sigma,num_tasks)
    deg2 = (deg/2.).astype(np.int)
    deg2 = np.clip(deg2,1,20)
    #add edges from top to down with deg2, then bottom-up with deg2
    edges = []
    # ---- top-down ----
    for ti in range(num_tasks):
        if level_per_task[ti] == num_level-1:   # exit task is a sink
            continue
        ti_lvl = level_per_task[ti]
        child_pool = []
        for li,tli in task_per_level.items():
            if li <= ti_lvl or li > ti_lvl+delta_lvl:
                continue
            child_pool += tli
        neighs_top_down[ti] = np.random.choice(child_pool,min(deg2[ti],len(child_pool)),replace=False)
        edges += [(str(ti),str(ci)) for ci in neighs_top_down[ti]]
    # ---- down-top ----
    for ti in reversed(range(num_tasks)):
        if level_per_task[ti] == 0:
            continue
        ti_lvl = level_per_task[ti]
        child_pool = []
        for li,tli in task_per_level.items():
            if li >= ti_lvl or li < ti_lvl-delta_lvl:
                continue
            child_pool += tli
        neighs_down_top[ti] = np.random.choice(child_pool,min(deg2[ti],len(child_pool)),replace=False)
        edges += [(str(ci),str(ti)) for ci in neighs_down_top[ti]]
    return list(set(edges)),neighs_top_down,neighs_down_top

def gen_chain_links(level_per_task):
    num_tasks = len(level_per_task)
    edges = []
    for i in range(num_tasks-1):
        edges += [(str(i),str(i+1))]
    return edges



def gen_attr(tasks,edges,ccr,comp_mu,comp_sigma,link_comm_sigma):
    task_comp = np.clip(np.random.normal(comp_mu,comp_sigma,len(tasks)), EPSILON, comp_mu+10*comp_sigma)
    link_comm = np.zeros(len(edges))
    link_comm_mu = comp_mu * ccr
    #link_comm is the data transmitted on links, comp is the computation workload. They both follow normal distribution. ccr is a constant
    link_comm = np.clip(np.random.normal(link_comm_mu,link_comm_sigma*link_comm_mu,len(edges)),EPSILON, link_comm_mu+10*link_comm_sigma*link_comm_mu)
    return task_comp,link_comm

def prepare_task_dag(config_yml,dag_path_plot):
    with open(config_yml) as f_config:
        config = yaml.load(f_config,Loader=yaml.FullLoader)
    #--- generate task graph ---

    task_per_level,level_per_task = gen_task_nodes(config['depth'],config['total_num'],config['width_min'],config['width_max'])

    if config['width_max'] > 1:
        edges,adj_list_top_down,adj_list_down_top = gen_task_links(config['deg_mu'],config['deg_sigma'],task_per_level,level_per_task)
    else:
        edges = gen_chain_links(level_per_task)

    
    #edges,adj_list_top_down,adj_list_down_top = gen_task_links(config['deg_mu'],config['deg_sigma'],task_per_level,level_per_task)
    
    task_comp,link_comm = gen_attr(np.arange(len(level_per_task)),edges,config['ccr'],config['comp_mu'],config['comp_sigma'],config['link_comm_sigma'])
    edge_d = [(e[0],e[1],{'data':link_comm[i]}) for i,e in enumerate(edges)]
    dag = nx.DiGraph()
    dag.add_edges_from(edge_d)
    for i,t in enumerate(task_comp):
        dag.nodes[str(i)]['comp'] = t
        ##NOTE: actually it should not be called 'comp', but 'computation data amount'!!!
    if dag_path_plot is not None:
        plot_dag(dag,dag_path_plot)
    
    return dag

def plot_dag(dag,dag_path_plot):
    pos = graphviz_layout(dag,prog='dot')
    node_labels = {n:'{}-{:3.1f}'.format(n,d['comp']) for n,d in dag.nodes(data=True)}
    edge_labels = {(e1,e2):'{:4.2f}'.format(d['data']) for e1,e2,d in dag.edges(data=True)}
    plt.clf()
    nx.draw(dag,pos=pos,labels=node_labels,font_size=8)
    nx.draw_networkx_edge_labels(dag,pos,edge_labels=edge_labels,label_pos=0.75,font_size=6)
    plt.savefig(dag_path_plot)

def generate_dag_config(dag,app_path):
    sorted_list = sorted(dag.nodes(data=True), key=lambda x: x[0], reverse=False)
    num_nodes = len(sorted_list)
    print("Number of nodes  in DAG : {}".format(num_nodes))
    f = open(app_path,'w')
    for i in dag.nodes():
        if i==str(num_nodes-1): #last_node playing the role of a sink only, not perform any comp or comm task
            f.write("task"+i)
        else:
            comp = round(sorted_list[int(i)][1]['comp'], 1)
            f.write("task"+i+ " "+str(comp)+" ")
            for e0,e1,d in dag.edges(data=True):
                if i == e0:
                    f.write('task'+e1+'-'+str(round(d['data'],2))+' ') #KB
        f.write("\n")
    f.close()


def generate_app_config(dag,dummy_yaml_path, input_file):
    data = load_yaml(input_file)

    data['application'] = dict()
    data['application']['tasks'] = dict()
    data['application']['tasks']['home'] = dict()
    data['application']['tasks']['home']['base_script'] = 'home.py'

    non_dag = dict()
    non_dag['name'] = 'datasource'
    non_dag['base_script'] = 'datasource.py'
    non_dag['children'] = ['task0']
    non_dag['k8s_host'] = data['node_map']['home'] 
    data['application']['tasks']['nondag_tasks'] = [non_dag]

    tasks = []
    data['application']['tasks']['dag_tasks'] = tasks
    sorted_list = sorted(dag.nodes(data=True), key=lambda x: x[0], reverse=False)
    num_nodes = len(sorted_list)
    print("Number of nodes  in DAG : {}".format(num_nodes))
    for i in range(num_nodes):
        tmp = dict()
        tmp['base_script'] = 'task.py'
        tmp['name'] = 'task{}'.format(i)
        tmp['children'] = []
        for e0,e1,d in dag.edges(data=True):
            if i == int(e0):
                tmp['children'].append('task'+e1)
        if len(tmp['children'])==0:
            tmp['children'] = ['home']   
        tasks.append(tmp)
        print(tmp)

    with open(dummy_yaml_path, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


def load_yaml(filename):
    """
    Parse yaml file into python dictionary

    :type       filename:  path to file
    :param      filename:  string

    :returns:   python dictionary of yaml contents
    :rtype:     dict
    """
    with open(filename) as f:
        config = yaml.load(f,Loader=yaml.FullLoader)
        logging.debug(config)
    return config
    



if __name__ == '__main__':
    args = parse_args()
    dummy_app_path = 'dummy/'
    dummy_dag_plot = dummy_app_path + 'dag.png'
    dummy_config_path = dummy_app_path + 'config.txt'
    dummy_yaml_path = dummy_app_path + 'app_config.yaml'
    input_file = 'input.yaml'
    
    if os.path.isdir(dummy_app_path):
      shutil.rmtree(dummy_app_path)
    copy_tree("base", "dummy")
    print('Create dummy_app folder, generate DAG and plot corresponding dag.png')
    dag= prepare_task_dag(args.conf,dummy_dag_plot)

    print('Generate config.txt')
    generate_dag_config(dag,dummy_config_path)

    print('Generate app_yaml file')
    generate_app_config(dag,dummy_yaml_path,input_file)
