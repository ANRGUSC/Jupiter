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


from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client as xmlrpclib
import socket
import fcntl
import struct
import multiprocessing
import numpy as np
import sys
import time
import json
import re
import os
import signal
import paramiko

configs = json.load(open('/centralized_scheduler/config.json'))
encoding = np.array(configs['matrixConfigs']['encoding'])
configs = json.load(open('/centralized_scheduler/config.json'))

masterid = configs['taskname_map'][os.environ['TASK']][2] 

k, n = encoding.shape

READY_SLAVES_NEEDED = n
CODING_COPIES_NEEDED = k 
CHUNKS = configs['chunks'] 
NUM_BINS = 64
all_nodes = os.environ["ALL_NODES"].split(":")
all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":")
node_dict = dict(zip(all_nodes, all_nodes_ips))


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', b'eth0')
    )[20:24])

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Register an instance; all the methods of the instance are
# published as XML-RPC methods (in this case, just 'div').
class MyFuncs:
    def __init__(self, token, ready):
        self.token = token
        self.ready = ready
        self.products = {}
        self.slavePids = {}
        self.readyCount = 0
 
    def slave_ready(self, slaveID):
        print("slave_ready")
        self.readyCount += 1
        print("slave %s is ready" % (slaveID))
        if self.readyCount >= READY_SLAVES_NEEDED:
            self.ready.clear()
            self.ready.set()
        return
   
    def checkDone(self):
        return len(self.products.keys()) >= CODING_COPIES_NEEDED
       
    def accept_pid(self, slave, pid):
        self.slavePids[slave] = pid

    def accept_product(self, product, partition):
        if len(self.products.keys()) < CODING_COPIES_NEEDED:
            self.products[partition] = product
        if len(self.products.keys()) >= CODING_COPIES_NEEDED:
            self.token.clear()
            self.token.set()
        return

    def clear(self):
        self.products = {}
        self.slavePids = {}
        self.token.clear()
        self.ready.clear()

    def retrieve_products(self):
        return self.products

    def retrieve_pids(self):
        return self.slavePids

class MasterServerProcess(multiprocessing.Process):
    quit = False
    def __init__(self, myIP, myPortNum, token, ready):
        multiprocessing.Process.__init__(self)
        #self.setDaemon(True)
        self.daemon = True
        self.server = SimpleXMLRPCServer((myIP, int(myPortNum)),
                                     requestHandler=RequestHandler, allow_none=True)
        self.server.register_introspection_functions()
        
        myFuncs = MyFuncs(token, ready)
        self.funcs = myFuncs
        self.server.register_instance(myFuncs)

    def run(self):
        # self.server.serve_forever()
        while not self.quit:
            self.server.handle_request()

    def stop_server(self):
        self.quit = True
        self.server.server_close()
        print("here")

        return 0

def encode_matrix(matrix, encoding):
    configs = json.load(open('/centralized_scheduler/config.json'))
    masterid = configs['taskname_map'][os.environ['TASK']][2] 
    k, n = encoding.shape
    splits = np.array_split(matrix, k)
    encodeds = []
    print("Configs", configs)
    for idx in range(n):
      code = encoding[:, idx]
      encoded = np.zeros_like(splits[0])
      for split_idx, coeff in enumerate(code):
          encoded += coeff * splits[split_idx]
      ptFile = '/home/darpa/apps/data/partition%d.mat' % (idx+1)
      slaveIP = node_dict['dftslave'+ str(masterid)+ str(idx)]
      print("Slaves_IP", slaveIP)
      np.savetxt(ptFile, encoded, fmt='%i')
      #cmd = "scp %s %s:%s" % (ptFile, slaveIP, ptFile)
      ssh = paramiko.SSHClient()
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      #Keep retrying in case the containers are still building/booting up o 
      #the child nodes.
      retry = 0
      num_retries = 30
      user = "root"
      password = "PASSWORD"
      ssh_port = 5000
      while retry < num_retries:
        try:
            ssh.connect(slaveIP, username=user, password=password, port=ssh_port)
            sftp = ssh.open_sftp()
            sftp.put(ptFile, ptFile)
            sftp.close()
            break
        except Exception as e:
            print('SSH Connection refused or File transfer failed, will retry in 2 seconds')
            print(e)
            time.sleep(5)
            retry += 1

      ssh.close()

      # while 1:
      #   try:
      #       cmd = "sshpass -p 'PASSWORD' scp -P 5000 -o StrictHostKeyChecking=no %s %s:%s" % (ptFile, slaveIP, ptFile) 
      #       print("cmd:", cmd)
      #       os.system(cmd)
      #       break
      #   except Exception as e:
      #       print("Sending the file failed. Will retry again!!!")
      #       print(e)
      encodeds.append(encoded)
    
    return encodeds   
   
def encode_matrix_tp(matrix, encoding):
    configs = json.load(open('/centralized_scheduler/config.json'))
    masterid = configs['taskname_map'][os.environ['TASK']][2] 
    k, n = encoding.shape
    splits = np.array_split(matrix, k)
    encodeds = []
    configs = json.load(open('/centralized_scheduler/config.json'))
    for idx in range(n):
      code = encoding[:, idx]
      encoded = np.zeros_like(splits[0])
      for split_idx, coeff in enumerate(code):
          encoded += coeff * splits[split_idx]
      ptFile = '/home/darpa/apps/data/partition%d_tp.mat' % (idx+1)
      slaveIP = node_dict['dftslave'+ str(masterid)+ str(idx)]
      np.savetxt(ptFile, encoded, fmt='%i')
      #cmd = "scp %s %s:%s" % (ptFile, slaveIP, ptFile) 
      ssh = paramiko.SSHClient()
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      #Keep retrying in case the containers are still building/booting up o 
      #the child nodes.
      retry = 0
      num_retries = 30
      user = "root"
      password = "PASSWORD"
      ssh_port = 5000
      while retry < num_retries:
        try:
            ssh.connect(slaveIP, username=user, password=password, port=ssh_port)
            sftp = ssh.open_sftp()
            sftp.put(ptFile, ptFile)
            sftp.close()
            break
        except Exception as e:
            print('SSH Connection refused or File transfer failed, will retry in 2 seconds')
            print(e)
            time.sleep(5)
            retry += 1

      ssh.close()

      encodeds.append(encoded)
    
    return encodeds   
         
 
def decode_products_generic(encoding, lookup, products, dim, k, n):
    result = np.zeros((dim, NUM_BINS), dtype=complex)
    p = re.compile('slave(\d+)')
    s = set(np.arange(k) + 1)
    cols = []
    slaveDict = {}
    for slave in sorted(products.keys(), key=lambda k: int(k[len('slave'):])):
        product = products[slave]
        ID = int(p.match(slave).group(1))
        cols.append(ID-1)
        slaveDict[ID-1] = product
        if ID <= k:
            start = int((ID - 1) * (dim/k))
            end = int(start + dim/k)
            if product.shape[0] != (dim/k):
                print(slave + ': race condition! Ignore for now.')
            else:
                result[start:end, :] = product
            s.remove(ID)
    for missing in s:
        start = int((missing - 1) * (dim/k))
        end = int(start + dim/k)
        result_list = np.array(np.split(result, k))
        encodedM = encoding[:, cols]
        encodedMstr = str(encodedM)
        if encodedMstr not in lookup.keys():
            lookup[encodedMstr] = np.linalg.inv(encodedM)
        encodedM_inv = lookup[encodedMstr]
        coeffs = encodedM_inv[:, missing-1]
        tmp = None
        for index in range(len(cols)):
            try:
                sId = cols[index]
                if not index:
                    tmp = coeffs[index] * slaveDict[sId]
                else:
                    tmp = tmp + (coeffs[index] * slaveDict[sId])
            except:
                print('race condition! Ignore for now.')
                
        result[start:end,:] = tmp 
    return result
       
def generateReplicasAndSpeeds(means):
    replicas = list(map(lambda m: int(np.round(1.0+np.random.exponential(m-1.0+0.1))), means))
    #replicas = means
    speeds = 1.0 / np.array(replicas)
    return replicas, speeds
             
def main():
    matrixMulKernelMaster()

def matrixMulKernelMaster(iteration=0, matrix=None, execTimes=None):
    #np.random.seed(1351)
    configs = json.load(open('/centralized_scheduler/config.json'))
    masterid = configs['taskname_map'][os.environ['TASK']][2] 

    #myIP = configs['masterConfigs']['IP']
    # TODO?? The IP is not correct is should be same as the service IP
    myIP = get_ip_address('eth0')
    myPortNum = configs['PortNum']

    start_time = time.time()
    global token, ready, server_process, encoding, encodeds, slaves, localProxy, dim

    # Create server
    if not iteration:
        token = multiprocessing.Event()
        ready = multiprocessing.Event()
        server_process = MasterServerProcess(myIP, myPortNum, token, ready) 
        server_process.start()
        print('starting master server process...')
        slaves = []
        encoding = np.array(configs['matrixConfigs']['encoding'])
        k, n = encoding.shape
        for i in range(n):
            slave = node_dict['dftslave'+ str(masterid)+str(i)] + ':' + configs['PortNum']
            print(slave)
            slaves.append(xmlrpclib.ServerProxy('http://' + slave, allow_none=True))

        localProxy = xmlrpclib.ServerProxy('http://' + myIP + ':' + myPortNum, allow_none=True)
        
   
        if matrix is None: 
            dim = configs['matrixConfigs']['dimension']
            matrix = np.random.rand(dim,dim)
        else:
            dim = matrix.shape[0]
        #encodeds = encode_matrix(matrix, encoding)
        
        #execTimes = configs['execTimes']

        end_time = time.time()
        start_time = end_time


    dim = matrix.shape[0]
    localProxy.clear()
    k, n = encoding.shape
    chunks = CHUNKS
    chunks_replicas = {i : [] for i in range(n)}
    chunks_rows = {i : [] for i in range(n)}
    chunks_lengths = {i : [] for i in range(n)}
    rows = [0 for i in range(n)]
    lengths = [((dim/k)/chunks) for i in range(n)]
    if not iteration:
        print("wait for all slaves to get ready")
        ready.wait()
    start_time = time.time()

    for chunk in range(chunks): 
        #ui = getSlaveSpeeds()
        replicas, ui = generateReplicasAndSpeeds(execTimes)
        print(replicas)
        rows_slave = np.array(rows)
        rows_slave = rows_slave + (chunk * (dim/k)/chunks)
        print(rows_slave, lengths)
        for i in range(n):
            chunks_replicas[i].append(replicas[i])
            chunks_rows[i].append(int(rows_slave[i]))
            chunks_lengths[i].append(int(lengths[i]))

    communication_time = 0
    c_time = time.time()
    # distribute the data
    for i in range(n):
      print(i)
      while True:
        try:
            slaves[i].accept_matrix(chunks_rows[i], chunks_lengths[i], chunks_replicas[i])
            break
        except Exception as e:
            print("getting matrix Failed. Will retry again!!!")
            print(e)
    for i in range(n): 
        slaves[i].start()
    communication_time += time.time() - c_time

    token.wait()
    productFileNames = localProxy.retrieve_products()
    print(productFileNames)
    end_time = time.time()
    computeTime = end_time - start_time - communication_time
    start_time = end_time

    products = {}
    p = re.compile('slave(\d+)')
    s = set(np.arange(n) + 1)
    for slave in sorted(productFileNames.keys()):
        ID = int(p.match(slave).group(1))
        s.remove(ID)
        products[slave] = np.loadtxt(productFileNames[slave]).view(complex)
        if len(products[slave].shape) < 2:
            products[slave] = products[slave].reshape(products[slave].shape[0], 1)

    #for i in s:
    #    print('releasing %d' % i)
    #    c_time = time.time()
    #    slaves[i-1].release()
    #    communication_time += time.time() - c_time
    
    lookup = {}
    #result = decode_products(products, dim, k, n)
    result = decode_products_generic(encoding, lookup, products, dim, k, n)
    end_time = time.time()
    decode_time = end_time - start_time
    
    localProxy.clear()

    server_process.stop_server()
    server_process.terminate()
    print("Stop Server Called")
    #verify = matrix.dot(np.arange(dim*dim).reshape(dim,dim) + 1)
    #print 'verifying results, maximum of the element difference is', np.max(np.abs(result-verify))
    return result, computeTime, communication_time, decode_time

if __name__ == '__main__':
    main()
