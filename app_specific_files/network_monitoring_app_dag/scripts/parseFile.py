"""
 * Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pranak Sakulkar, October 2017
 *      Jiatong Wang, October 2017
 *      Aleksandra Knezevic, October 2017
 *      Bhaskar Krishnamachari, October 2017
 *     Read license file in main directory for more details  
"""


from __future__ import print_function
from __future__ import division
import numpy as np
import sys

def readFile(fileName, numBins):
    timeT = {}
    ips = set([])
    f = open(fileName, 'r')
    total = 0
    numData = 0
    for line in f:
        if line.startswith('!'):
            continue
        numData += 1
        timestamp,ip_src,sport,ip_dst,dport,ip_len,ip_proto,tcp_flags = line.split()
        timestamp = float(timestamp)
        ip_len = int(ip_len)
        total += ip_len
        ips.add(ip_src)
        ips.add(ip_dst)
        if timestamp not in timeT:
            timeT[timestamp] = []
        timeT[timestamp].append([ip_src,sport,ip_dst,dport,ip_len])
    allTSs = sorted(timeT.keys())
    delta = (allTSs[-1] - allTSs[0]) / numBins
    intervalPoints = np.arange(allTSs[0]+delta, allTSs[-1]+delta, delta)
    #allTSs[-1] += 0.1 * delta
    #print(allTSs[0], allTSs[-1], delta, intervalPoints[-1])    
    #print(intervalPoints)
    ipMap = {}
    idx = 0
    for ip in sorted(ips):
        ipMap[ip] = idx
        idx += 1
    matrix = np.zeros((numBins, len(ipMap) * 2))
    start = 0
    for idx, threshold in enumerate(intervalPoints):
        cnt = 0
        for ts in allTSs[start:]:
            if ts < threshold:
                for ip_src,sport,ip_dst,dport,ip_len in timeT[ts]:
                    matrix[idx, ipMap[ip_src]] += ip_len
                    matrix[idx, len(ipMap) + ipMap[ip_dst]] += ip_len
                cnt += 1
            else:
                break
        start += cnt
    # put the remaining to the last bin 
    for ts in allTSs[start:]:
        for ip_src,sport,ip_dst,dport,ip_len in timeT[ts]:
            matrix[(numBins-1), ipMap[ip_src]] += ip_len
            matrix[(numBins-1), len(ipMap) + ipMap[ip_dst]] += ip_len
            
    f.close()
    matrix = matrix.astype(int)
    print(total*2, matrix.sum())
    return matrix.T, sorted(ips), intervalPoints[0], intervalPoints[-1]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Need to provide the file name for parsing')
    else:
        fileName = sys.argv[1]
        numBins = int(sys.argv[2])
        matrix = readFile(fileName, numBins)
        print(matrix)
        print(matrix.sum(axis=0))
        print(matrix.sum(axis=1))

