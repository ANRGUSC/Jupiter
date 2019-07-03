
from heapq import nsmallest
    #num: select k neighbors near the node based on shorted distance
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
num = 3
connected = {}
for city in reg:
    pairs = [k for k,v in distance.items() if k[0]==city or k[1]==city]
    nb = dict((k, distance[k]) for k in pairs)
    neigbors = nsmallest(num, nb, key = nb.get)
    for item in neigbors:
        connected[item] = 1
        connected[(item[1],item[0])] = 1

cluster = {}
all_node_geo = {'nyc': ['node111', 'node99', 'node73', 'node81', 'node110', 'node52', 'node71', 'node43', 'node13', 'node67', 'node92', 'node21', 'node76', 'node10', 'node8', 'node102', 'node98', 'node33', 'node75'], 'blr': ['node14', 'node64', 'node93', 'node30', 'node51', 'node104', 'node74', 'node49', 'node85', 'node45', 'node5'], 'lon': ['node16', 'node62', 'node27', 'node58', 'node69', 'node61', 'node7', 'node2', 'node29', 'node78', 'node106', 'node19', 'node77', 'node23', 'node57', 'node97'], 'sgp': ['node108', 'node44', 'node47', 'node40', 'node28', 'node36', 'node70', 'node65', 'node89'], 'tor': ['node103', 'node86', 'node80', 'node56', 'node87', 'node37', 'node94', 'node41', 'node63', 'node101'], 'sfo': ['node3', 'node107', 'node95', 'node53', 'node90', 'node54', 'node39', 'node72', 'node11', 'node79', 'node59', 'node100', 'node25'], 'ams': ['node55', 'node42', 'node46', 'node88', 'node35', 'node96', 'node68', 'node24', 'node66', 'node82', 'node60', 'node9'], 'fra': ['node48', 'node91', 'node18', 'node15', 'node83', 'node12', 'node32', 'node26', 'node50', 'node31', 'node34', 'node17', 'node6', 'node20', 'node38']}

for geo in all_node_geo:
    print('----------')
    print(geo)
    cluster[geo] = all_node_geo[geo]
    nbs = [k[1] for k,v in connected.items() if v==1 and (k[0]==geo)]
    print(nbs)
    for nb in nbs:
        cluster[geo].extend(all_node_geo[nb])

print(cluster[geo])