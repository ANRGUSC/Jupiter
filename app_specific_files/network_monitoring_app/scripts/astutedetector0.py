"""
 * Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pranav Sakulkar, October 2017
 *      Jiatong Wang, October 2017
 *      Aleksandra Knezevic, October 2017
 *      Bhaskar Krishnamachari, October 2017
 *     Read license file in main directory for more details
"""

import sys
import numpy as np
import os
import struct
from collections import defaultdict
import collections
import itertools
import numpy as np
from copy import deepcopy
import types
import time


try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str, bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring


def constant_factory():
    return lambda: np.zeros(2)


def task(filename, pathin, pathout):

    time.sleep(15)

    num = filename.partition('m')[0]
    thres = 3.0
    binSize = 10

    binStart = 0
    previousBin = None  # Volume at the 6 flow aggregation levels: 5-tuple, IP pairs, src. IP, dst. IP, src. port, dst. port
    currentBin = None

    pktPerHost = dict()

    # read and parse file
    with open(os.path.join(pathin, filename), 'r') as f:
        for line in f:

            if line.startswith("!"):
                continue

            # get each fields of the tuple
            words = line.split()


            ts = float(words[0])
            ipSrc = words[1]
            try:
                portSrc = int(words[2])
            except ValueError:
                portSrc = 0

            ipDst = words[3]
            try:
                portDst = int(words[4])
            except ValueError:
                portDst = 0

            bytes = int(words[5])
            proto = words[6]

            if ts > binStart + binSize:

                if currentBin:
                    saveCurrentBin = deepcopy(currentBin)

                if previousBin:

                    K = np.zeros((6, 2))
                    allKeys = []
                    delta = []

                    mean = np.zeros((6, 2))
                    std = np.zeros((6, 2))



                    for i in range(6):
                        # Compute the volume changes
                        if i < 4:

                            allKeys.append(list(set(list(previousBin[i].keys()) + list(currentBin[i].keys()))))
                            delta.append(np.array([currentBin[i][k] - previousBin[i][k] for k in allKeys[i]]))

                        else:  # port information are kept in ndarray
                            allKeys.append(list(set(
                                np.nonzero(previousBin[i][:, 0])[0].tolist() + np.nonzero(currentBin[i][:, 0])[
                                    0].tolist())))
                            delta.append(np.array([currentBin[i][k] - previousBin[i][k] for k in allKeys[i]]))

                        mean[i] = np.mean(delta[i], 0)
                        std[i] = np.std(delta[i], 0)

                        # testsub = delta[i]
                        # F= np.size(delta[i], 0);
                        # Compute K'

                        K[i, :] = mean[i] * np.sqrt(np.size(delta[i], 0)) / std[i]

                    anomalous = [[], []]
                    noAnomaly = [[], []]
                    for volType in range(2):
                        anomalous[volType], = np.nonzero(abs(K[:, volType]) > thres)
                        noAnomaly[volType], = np.nonzero(abs(K[:, volType]) <= thres)

                    ##### Flow identification #####

                    for volType in range(2):
                        anomalousFeature = []
                        volAno = 0
                        for ano in anomalous[volType]:
                            lowerBound = mean[ano, volType] - thres * std[ano, volType] * np.sqrt(np.size(delta[i], 0))
                            upperBound = mean[ano, volType] + thres * std[ano, volType] * np.sqrt(np.size(delta[i], 0))

                            if abs(lowerBound) > abs(upperBound):
                                volAno = lowerBound
                            else:
                                volAno = upperBound

                        if volAno:
                            top = 25
                            volCount = np.zeros(6)
                            anomalousFeature = [[], [], [], [], [], []]
                            anoFound = -1

                            while anoFound == -1 and top < 100:  # no more than 100 features per anomaly
                                for flowAgg in noAnomaly[volType]:
                                    inc = 0
                                    while abs(volCount[flowAgg]) < abs(volAno) and inc < top:
                                        if volAno < 0:
                                            anoFlow = np.argmin(delta[flowAgg][:, volType])
                                        else:
                                            anoFlow = np.argmax(delta[flowAgg][:, volType])

                                        if not (flowAgg in [4, 5] and allKeys[flowAgg][
                                            anoFlow] < 100):  # ignore only port 80 or 0 kind of anomaly
                                            volCount[flowAgg] += delta[flowAgg][anoFlow, volType]
                                            anomalousFeature[flowAgg].append(allKeys[flowAgg][anoFlow])
                                        delta[flowAgg][anoFlow, volType] = 0
                                        inc += 1

                                if np.any(abs(volCount) >= abs(volAno)):
                                    anoFound = np.nonzero(abs(volCount) >= abs(volAno))[0][0]

                                top += top  # try again with more flows

                                for flow in anomalousFeature[anoFound]:
                                    srcIP = "*"
                                    dstIP = "*"
                                    srcPort = "*"
                                    dstPort = "*"
                                    proto = "*"

                                    if anoFound == 0:
                                        srcIP = flow[0]
                                        dstIP = flow[1]
                                        if flow[2]: srcPort = str(flow[2])
                                        if flow[3]: dstPort = str(flow[3])
                                        proto = flow[4]
                                    elif anoFound == 1:
                                        srcIP = flow[0]
                                        dstIP = flow[1]
                                    elif anoFound == 2:
                                        srcIP = flow
                                    elif anoFound == 3:
                                        dstIP = flow
                                    elif anoFound == 4:
                                        srcPort = str(flow)
                                    elif anoFound == 5:
                                        dstPort = str(flow)

                                    str_all = srcIP + ":" + srcPort + " " + dstIP + ":" + dstPort + ";" + str(
                                        binStart) + ";" + str(binStart + binSize)

                                    if anoFound != -1:
                                        if str_all in pktPerHost:
                                            pktPerHost[str_all] += 1
                                        else:
                                            pktPerHost[str_all] = 1

                if binStart == 0:  # first time in the loop
                    binStart = ts
                if currentBin:
                    previousBin = saveCurrentBin

                currentBin = [defaultdict(constant_factory()), defaultdict(constant_factory()),
                              defaultdict(constant_factory()), defaultdict(constant_factory()), np.zeros((2 ** 16, 2)),
                              np.zeros((2 ** 16, 2))]

                binStart += binSize

            inc = np.array([1, bytes])

            # update the counters for the 5-tuple
            currentBin[0][(ipSrc, ipDst, portSrc, portDst, proto)] += inc
            # update the counters for the pair of IP
            currentBin[1][(ipSrc, ipDst)] += inc
            # update the counters for the src. IP
            currentBin[2][ipSrc] += inc
            # update the counters for the dst. IP
            currentBin[3][ipDst] += inc
            # update the counters for the ports
            currentBin[4][portSrc] += inc
            currentBin[5][portDst] += inc

    with open(os.path.join(pathout, num+'anomalies_astute0.log'), 'w') as writefile:
        for key, value in pktPerHost.items():
            writefile.write(key + '\n')

    return [os.path.join(pathout, num+'anomalies_astute0.log')]
def main():

    filelist = '25merged_file0.ipsum'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':

    filename = '25merged_file0.ipsum'
    task(filename, '/home/apac/security_app', '/home/apac/security_app')
