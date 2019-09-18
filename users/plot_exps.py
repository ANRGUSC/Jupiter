__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import matplotlib.pyplot as plt
from collections import OrderedDict
import os
from statistics import mean 
import networkx as nx
from heapq import nsmallest
import sys
import shutil
import time
sys.path.append("../")
import jupiter_config
sys.path.append("../mulhome_scripts/")
import utilities
import pandas as pd


### Results at : https://docs.google.com/presentation/d/1tUOp1AOqo_860HVYYpcATOGrR5aKRfKB5jV3bRT4m88/edit?pli=1#slide=id.g62ba74cb4d_1_4


def plot_nodes():
        node_file = 'nodes.txt'
        geo = dict()
        with open(node_file) as f:
                lines = f.readlines()
                for line in lines:
                        info = line.strip().split(' ')
                        tmp = info[1].split('-')[-1][0:3]
                        if tmp not in geo:
                                geo[tmp] = 1
                        else:
                                geo[tmp] = geo[tmp]+1
        print(geo) 
        count = sum(geo.values())
        plt.pie([float(v) for v in geo.values()], labels=[str(k) for k in geo.keys()], autopct='%1.0f%%')
        title = 'Digital Ocean Node Setting : %d nodes'%(count)
        plt.title(title)
        plt.show()

def plot_clusters(num):
        distance = {}
        distance[('lon','tor')] = 8
        distance[('lon','fra')] = 1.5
        distance[('lon','sgp')] = 13
        distance[('lon','blr')] = 10
        distance[('lon','ams')] = 1
        distance[('lon','sfo')] = 11
        distance[('lon','nyc')] = 8
        distance[('tor','fra')] = 8.5
        distance[('tor','sgp')] = 20.5
        distance[('tor','blr')] = 19.5 
        distance[('tor','ams')] = 7
        distance[('tor','sfo')] = 5
        distance[('tor','nyc')] = 1.5
        distance[('fra','sgp')] = 12.5
        distance[('fra','blr')] = 9.5
        distance[('fra','ams')] = 1
        distance[('fra','sfo')] = 11
        distance[('fra','nyc')] = 8.5
        distance[('sgp','blr')] = 4.5 
        distance[('sgp','ams')] = 13
        distance[('sgp','sfo')] = 16.5
        distance[('sgp','nyc')] = 18.5
        distance[('blr','ams')] = 12
        distance[('blr','sfo')] = 22
        distance[('blr','nyc')] = 19.5
        distance[('ams','sfo')] = 10.5
        distance[('ams','nyc')] = 8
        distance[('nyc','sfo')] = 5.5

        reg = ['lon','tor','fra','sgp','blr','ams','sfo','nyc']
        connected = {}
        G=nx.Graph()
        G.add_nodes_from(reg)
        for city in reg:
                pairs = [k for k,v in distance.items() if k[0]==city or k[1]==city]
                nb = dict((k, distance[k]) for k in pairs)
                neigbors = nsmallest(num, nb, key = nb.get)
                for item in neigbors:
                        connected[item] = 1
                        connected[(item[1],item[0])] = 1
                        G.add_edge(item[0],item[1])


        nx.draw(G,with_labels=True)
        plt.show() # display




def exp1():
        #Experiment 1 Makespan
        B = {'9botnet.ipsum': 137.30246877670288, '7botnet.ipsum': 137.71886897087097, '2botnet.ipsum': 138.34141039848328, '3botnet.ipsum': 137.6883101463318, '8botnet.ipsum': 138.2628936767578, '10botnet.ipsum': 137.32285976409912, '5botnet.ipsum': 137.38104581832886, '1botnet.ipsum': 138.6391270160675, '6botnet.ipsum': 137.280699968338, '4botnet.ipsum': 137.23282027244568}
        D = OrderedDict(sorted(B.items(), key=lambda t: t[0]))

        title = 'Experiment 1: Makespan (100-tasks DAG)'
        xlabel = 'Incoming files'
        ylabel = 'sec'
        plt.bar(range(len(D)), list(D.values()), align='center')
        plt.xticks(range(len(D)), list(D.keys()))
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()


def exp2():
        # Experiment 2 Makespan
        exp2_path = 'exp2_bu'
        makespan = dict()
        count = dict()
        for (dirpath, dirnames, filenames) in os.walk(exp2_path):
                for filename in filenames:
                      fname = os.path.join(dirpath,filename)
                      with open(fname,'r') as f:
                              l = [[st for st in line.strip().split(' ')] for line in f]
                              if len(l)>0:
                                      appname = l[0][1]
                                      appid = appname.split('dummyapp')[1]
                                      ms = [float(x[3]) for x in l]
                                      count[appid] = len(ms)
                                      makespan[appid] = mean(ms)

        print(makespan)
        print(count)
        print(len(makespan))
        sorted_makespan = OrderedDict(sorted(makespan.items(), key=lambda t: t[1]))
        print(sorted_makespan)
        title = 'Experiment 2: Makespan (100 DAGs)'
        xlabel = 'Application name'
        ylabel = 'sec'
        plt.bar(range(len(sorted_makespan)), list(sorted_makespan.values()), align='center')
        plt.xticks(range(len(sorted_makespan)), list(sorted_makespan.keys()))
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation='vertical')
        plt.show()

def exp3():
        # Experiment 3 Makespan
        exp3_path = 'exp3_bu'
        makespan = dict()
        count = dict()
        for (dirpath, dirnames, filenames) in os.walk(exp3_path):
                for filename in filenames:
                      fname = os.path.join(dirpath,filename)
                      with open(fname,'r') as f:
                              l = [[st for st in line.strip().split(' ')] for line in f]
                              if len(l)>0:
                                      appname = l[0][1]
                                      appid = appname.split('dummyapp')[1]
                                      ms = [float(x[3]) for x in l]
                                      count[appid] = len(ms)
                                      makespan[appid] = mean(ms)

        print(makespan)
        print(count)
        sorted_makespan = OrderedDict(sorted(makespan.items(), key=lambda t: t[1]))
        print(sorted_makespan)
        title = 'Experiment 3: Makespan (100 DAGs)'
        xlabel = 'Application name'
        ylabel = 'sec'
        plt.bar(range(len(sorted_makespan)), list(sorted_makespan.values()), align='center')
        plt.xticks(range(len(sorted_makespan)), list(sorted_makespan.keys()))
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation='vertical')
        plt.show()

def exp4():

        # Experiment 4 Overhead
        num_tasks = 30
        dir_path = os.path.dirname(os.path.realpath(__file__))
        exp4_path = os.path.join(dir_path,'exp4_30/')
        print(exp4_path)
        outfile = 'combined_%s.log'%(num_tasks)
        count = 0
        s = set() #one time mapping decision, remove redundant logging 
        for (dirpath, dirnames, filenames) in os.walk(exp4_path):
                for filename in filenames:
                        fname = os.path.join(dirpath,filename)
                        print(fname)
                        with open(fname,'r') as f:
                                lines = f.readlines()
                                for line in lines:
                                        print(line)
                                        if line not in s:
                                                s.add(line)
                                                c = int(line.split(' ')[3])
                                                count = count +c
        print(s)
        print(count)
        with open(outfile, 'w') as f:
            for item in s:
                f.write("%s" % item)


def exp67():
    jupiter_config.set_globals()

    # path1 = jupiter_config.APP_PATH + 'configuration.txt'
    # path2 = jupiter_config.HERE + 'nodes.txt'
    # path1 = '../app_specific_files/dummy_app/configuration.txt'
    # path2 = '../nodes_test.txt'


    # dag_info = utilities.k8s_read_dag(path1)
    # nodes = utilities.k8s_get_nodes(path2)
    # dag = dag_info[1]
    # N = len(nodes)
    # M = len(dag)

    path2 = '../nodes.txt'
    nodes = utilities.k8s_get_nodes(path2)
    N = 106
    M = 201

    overhead_latency_file = 'exp8_data/overheadlatency/system_latency_N%d_M%d.log'%(N,M)
    print(overhead_latency_file)

    time_stamp = {}
    with open(overhead_latency_file) as f:
        lines = f.readlines()
        for line in lines:
            info = line.strip().split(' ')
            key = (info[0],info[1])
            if key not in time_stamp:
                time_stamp[key] = [float(info[2])]
            else:
                time_stamp[key].append(float(info[2]))
            
    # print(time_stamp)

    power_overhead_folder = 'exp8_data/poweroverhead'
    power = {}
    c = 0
    for node in nodes:
        log_file = '%s/M%d/%s_N%d_M%d.log'%(power_overhead_folder,M,node,N,M)
        # log_file = '%s/%s_N%d_M%d.log'%(power_overhead_folder,node,N,M)
        print(log_file)
        with open(log_file) as f:
            lines = f.readlines()
            for line in lines:
                info = line.strip().split(' ')
                power[c] = [node,float(info[7]),float(info[3]),float(info[5])]
                c = c+1

    #Order: DRUPE - WAVE - CIRCE - EP - HEFT - CIRCE
    # DRUPE
    # t1 = time_stamp[('DRUPE','deploystart')][0]
    t2 = time_stamp[('WAVE','deploystart')][0]
    t3 = time_stamp[('CIRCE','deploystart')][0]
    t4 = time_stamp[('WAVE','teardownend')][0]
    t5 = time_stamp[('Executionprofiler','deploystart')][0]
    t6 = time_stamp[('HEFT','deploystart')][0]
    t7 = time_stamp[('CIRCE','deploystart')][1]
    t8 = time_stamp[('CIRCE','teardownend')][1]


    
    
    powerDF = pd.DataFrame.from_dict(power,orient='index')
    powerDF.columns = ['node', 'timestamp', 'cpu','memory']
    powerDF['type'] = powerDF.apply(lambda row: row['node'][0:4], axis=1)
    ntype = ['home','node']
    cpu_list = {}
    mem_list = {}


    for nt in ntype:
        # cpu_list[0,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t1) & (powerDF['timestamp']<=t2),'cpu']
        # mem_list[0,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t1) & (powerDF['timestamp']<=t2),'memory']
        cpu_list[1,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t2) & (powerDF['timestamp']<=t3),'cpu']
        mem_list[1,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t2) & (powerDF['timestamp']<=t3),'memory']
        cpu_list[2,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t3) & (powerDF['timestamp']<=t4),'cpu']
        mem_list[2,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t3) & (powerDF['timestamp']<=t4),'memory']
        cpu_list[3,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t5) & (powerDF['timestamp']<=t6),'cpu']
        mem_list[3,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t5) & (powerDF['timestamp']<=t6),'memory']
        cpu_list[4,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t6) & (powerDF['timestamp']<=t7),'cpu']
        mem_list[4,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t6) & (powerDF['timestamp']<=t7),'memory']
        cpu_list[5,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t7) & (powerDF['timestamp']<=t8),'cpu']
        mem_list[5,nt] = powerDF.loc[(powerDF['type']==nt) & (powerDF['timestamp']>=t7) & (powerDF['timestamp']<=t8),'memory']


    # Stage 1: [t1,t2] DRUPE 
    # Stage 2: [t2,t3] DRUPE + WAVE
    # Stage 3: [t3,t4] DRUPE + WAVE + CIRCE
    # Stage 4: [t5,t6] DRUPE + EP
    # Stage 5: [t6,t7] DRUPE + EP + HEFT
    # Stage 6: [t7,t8] DRUPE + EP + HEFT + CIRCE
    # Node type: 'home' or workers('node')
    
    print('------- CPU HOME ---------')
    nt = 'home'
    # print('DRUPE :'+ str(mean(cpu_list[0,nt])))
    print('DRUPE + WAVE :' + str(mean(cpu_list[1,nt])))
    print('DRUPE + WAVE + CIRCE :' + str(mean(cpu_list[2,nt])))
    print('DRUPE + EP :' +str(mean(cpu_list[3,nt])))
    print('DRUPE + EP + HEFT : ' +str(mean(cpu_list[4,nt])))
    print('DRUPE + EP + HEFT + CIRCE :' +str(mean(cpu_list[5,nt])))
    print('------- CPU WORKERS ---------')
    nt = 'node'
    # print('DRUPE : '+ str(mean(cpu_list[0,nt])))
    print('DRUPE + WAVE :' + str(mean(cpu_list[1,nt])))
    print('DRUPE + WAVE + CIRCE :' + str(mean(cpu_list[2,nt])))
    print('DRUPE + EP :' +str(mean(cpu_list[3,nt])))
    print('DRUPE + EP + HEFT :' +str(mean(cpu_list[4,nt])))
    print('DRUPE + EP + HEFT + CIRCE :' +str(mean(cpu_list[5,nt])))
    print('------- MEM HOME ---------')
    nt = 'home'
    # print('DRUPE :'+ str(mean(mem_list[0,nt])))
    print('DRUPE + WAVE :' + str(mean(mem_list[1,nt])))
    print('DRUPE + WAVE + CIRCE :'+ str(mean(mem_list[2,nt])))
    print('DRUPE + EP :' +str(mean(mem_list[3,nt])))
    print('DRUPE + EP + HEFT :' +str(mean(mem_list[4,nt])))
    print('DRUPE + EP + HEFT + CIRCE: ' +str(mean(mem_list[5,nt])))
    print('------- MEM WORKERS ---------')
    nt = 'node'
    # print('DRUPE :'+ str(mean(mem_list[0,nt])))
    print('DRUPE + WAVE :' + str(mean(mem_list[1,nt])))
    print('DRUPE + WAVE + CIRCE :' + str(mean(mem_list[2,nt])))
    print('DRUPE + EP :' +str(mean(mem_list[3,nt])))
    print('DRUPE + EP + HEFT :' +str(mean(mem_list[4,nt])))
    print('DRUPE + EP + HEFT + CIRCE: ' +str(mean(mem_list[5,nt])))
    


if __name__ == '__main__':
    exp67()

