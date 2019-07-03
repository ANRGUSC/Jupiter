import matplotlib.pyplot as plt
from collections import OrderedDict
import os
from statistics import mean 
import networkx as nx
from heapq import nsmallest


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
        num_tasks = 816
        dir_path = os.path.dirname(os.path.realpath(__file__))
        exp4_path = os.path.join(dir_path,'exp4_full_816/')
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


if __name__ == '__main__':
      # plot_clusters(3)
      exp4()

