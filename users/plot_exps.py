import matplotlib.pyplot as plt
from collections import OrderedDict
import os
from statistics import mean 

# #Experiment 1 Makespan
# B = {'9botnet.ipsum': 137.30246877670288, '7botnet.ipsum': 137.71886897087097, '2botnet.ipsum': 138.34141039848328, '3botnet.ipsum': 137.6883101463318, '8botnet.ipsum': 138.2628936767578, '10botnet.ipsum': 137.32285976409912, '5botnet.ipsum': 137.38104581832886, '1botnet.ipsum': 138.6391270160675, '6botnet.ipsum': 137.280699968338, '4botnet.ipsum': 137.23282027244568}
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



# Experiment 2 Makespan
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
# print(len(makespan))
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

#Experiment 3 Makespan
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
