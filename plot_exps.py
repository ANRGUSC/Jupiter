import matplotlib.pyplot as plt
from collections import OrderedDict
import os
from statistics import mean 

#Experiment 1 Makespan
# B = {'10botnet.ipsum': 104.53915619850159, '8botnet.ipsum': 104.4059100151062, '2botnet.ipsum': 104.58935880661011, '5botnet.ipsum': 104.04564428329468, '6botnet.ipsum': 104.37079286575317, '7botnet.ipsum': 107.29788970947266, '3botnet.ipsum': 104.47786402702332, '1botnet.ipsum': 106.05324864387512, '9botnet.ipsum': 104.63074469566345, '4botnet.ipsum': 103.99546027183533}
# D = OrderedDict(sorted(B.items(), key=lambda t: t[0]))

# title = 'Experiment 1: Makespan (100-tasks DAG)'
# xlabel = 'Incoming files'
# ylabel = 'sec'
# plt.bar(range(len(D)), list(D.values()), align='center')
# plt.xticks(range(len(D)), list(D.keys()))
# plt.title(title)
# plt.xlabel(xlabel)
# plt.ylabel(ylabel)
# plt.show()

#Experiment 1 Tasks


#Experiment 2 Makespan
# exp2_path = 'users/exp2_bu'
# makespan = dict()
# count = dict()
# for (dirpath, dirnames, filenames) in os.walk(exp2_path):
#         for filename in filenames:
#         	fname = os.path.join(dirpath,filename)
#         	with open(fname,'r') as f:
#         		l = [[st for st in line.strip().split(' ')] for line in f]
#         		if len(l)>0:
#         			appname = l[0][1]
#         			appid = appname.split('dummyapp')[1]
#         			ms = [float(x[3]) for x in l]
#         			count[appid] = len(ms)
#         			makespan[appid] = mean(ms)

# print(makespan)
# print(count)
# sorted_makespan = OrderedDict(sorted(makespan.items(), key=lambda t: t[1]))
# print(sorted_makespan)
# title = 'Experiment 2: Makespan (100 DAGs)'
# xlabel = 'Application name'
# ylabel = 'sec'
# plt.bar(range(len(sorted_makespan)), list(sorted_makespan.values()), align='center')
# plt.xticks(range(len(sorted_makespan)), list(sorted_makespan.keys()))
# plt.title(title)
# plt.xlabel(xlabel)
# plt.ylabel(ylabel)
# plt.xticks(rotation='vertical')
# plt.show()

#Experiment 2 Makespan
exp3_path = 'users/exp3_bu'
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
