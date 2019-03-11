"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 * Developed by:
 * Autonomous Networks Research Group (ANRG)
 * University of Southern California
 * http://anrg.usc.edu/
 *
 * Contributors:
 * Pranav Sakulkar,
 * Pradipta Ghosh,
 * Aleksandra Knezevic,
 * Jiatong Wang,
 * Quynh Nguyen,
 * Jason Tran,
 * H.V. Krishna Giri Narra,
 * Zhifeng Lin,
 * Songze Li,
 * Ming Yu,
 * Bhaskar Krishnamachari,
 * Salman Avestimehr,
 * Murali Annavaram
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * with the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * - Redistributions of source code must retain the above copyright notice, this
 *     list of conditions and the following disclaimers.
 * - Redistributions in binary form must reproduce the above copyright notice,
 *     this list of conditions and the following disclaimers in the
 *     documentation and/or other materials provided with the distribution.
 * - Neither the names of Autonomous Networks Research Group, nor University of
 *     Southern California, nor the names of its contributors may be used to
 *     endorse or promote products derived from this Software without specific
 *     prior written permission.
 * - A citation to the Autonomous Networks Research Group must be included in
 *     any publications benefiting from the use of the Software.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH
 * THE SOFTWARE.
"""

import json
import numpy as np
from masterServerStatic import matrixMulKernelMaster
from masterServerStatic import encode_matrix
from masterServerStatic import encode_matrix_tp
import multiprocessing
import time
import os
import math
from parseFile import readFile

NUM_BINS = 64
THRESHOLD = 56
all_nodes = os.environ["ALL_NODES"].split(":")
all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":")
node_dict = dict(zip(all_nodes, all_nodes_ips))
print(node_dict)

# def updateConfig():
#     # os.system('mkdir -p /home/darpa/apps/data')
#     # newIps_list = os.environ['DFT_NODES'].split("@")
#     # newIps = newIps_list[0].split(':')
#     # numSlaves = 3

#     configs = json.load(open('/centralized_scheduler/config.json'))
#     configs['masterConfigs']['IP'] = os.environ['OWN_IP']
#     for i in range(configs['nos_slave']):
#         configs['slaveConfigs']['slave'+str(i + 1)]['IP'] = node_dict['dftslave2' + str(i)]

#     json.dump(configs, open('/centralized_scheduler/config.json', 'w'))

def DFTMatrix(N):
    i,j = np.meshgrid(np.arange(N), np.arange(N), indexing = 'ij') #indexing 'ij' since matrix co-ord.
    omega = np.exp(-2 * math.pi * 1J/N)
    W = np.power(omega,i*j)/math.sqrt(1)
    return W

def computeDFT(dataset, execTimes):
    result, compute_time, communication_time, decode_time = matrixMulKernelMaster(0, dataset, execTimes)
    #weights = DFTMatrix(NUM_BINS)
    #verify = dataset.dot(weights)
    #print 'verifying results, maximum of the element difference is', np.max(np.abs(result-verify))
    return result, compute_time, communication_time, decode_time

def createOutput(result, ips, timestampS, timestampE):
    threshold = abs(result[:, THRESHOLD:])
    energy = threshold.sum(axis=1)
    badIP1 = ips[energy[0:int(len(energy)/2)].argmax()]
    badIP2 = ips[energy[int(len(energy)/2):].argmax()]
    #return '%f %s\n%f %s\n' % (timestamp, badIP1, timestamp, badIP2)
    return '%s:* *:*;%f;%f\n*:* %s:*;%f;%f\n' % (badIP1, timestampS, timestampE, badIP2, timestampS, timestampE)

def task(filename, pathin, pathout):
    # updateConfig()
    num = filename.partition('m')[0]
    configs = json.load(open('/centralized_scheduler/config.json'))
    encoding = np.array(configs['matrixConfigs']['encoding'])
    CHUNKS = configs['chunks']
    execTimes = configs['execTimes']
    k, n = encoding.shape
    output = ""
    time.sleep(5)
    try:
        X,ips,timestampS, timestampE = readFile(pathin+'/'+filename, NUM_BINS)
        partitions = encode_matrix(X, encoding)
        result, computeT, communicationT, decodeT = computeDFT(X, execTimes)
        output = createOutput(result, ips, timestampS, timestampE)
    except Exception as e:
        print("failed. details: " + str(e))        
    outFile = open(pathout + '/' + str(num) +  'anomalies_dft2.log', 'w')
    outFile.write(output)
    outFile.close()
    fileOut = pathout + '/' + str(num) +  'anomalies_dft2.log'
    return [fileOut]

def main():

    filelist = '25merged_file2.ipsum'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile

# def main():
#     task('1botnet.ipsum', './', './output.out')

if __name__ == '__main__':
    main()

