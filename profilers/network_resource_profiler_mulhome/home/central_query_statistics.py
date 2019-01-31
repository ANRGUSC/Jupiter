"""
    This Script allows querrying network profiling information updated from the cenetral mongo database, table ``central_network_profiler``.
"""
__author__ = "Quynh Nguyen, Pradipta Ghosh, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import csv
import pymongo
from pymongo import MongoClient
import pandas as pd
import json
import sys
import numpy as np
import configparser
from os import path




class central_query_statistics():
    def __init__(self):
        self.client_mongo = None
        self.db = None
    def do_query_quaratic(self,source,destination,file_size):
        """Query network profiling information and use these info to predict transfer time given source node, destination node and file size.
        
        Args:
            -   source (str): source IP address
            -   destination (str): destination IP address
            -   file_size (int): file size [Bytes]
        
        Returns:
            float: predicted transfer time [seconds]
        """

        self.client_mongo = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/') 
        self.db = self.client_mongo.central_network_profiler
        predicted = None
        relation_info = 'central_input/nodes.txt'
        df_rel = pd.read_csv(relation_info, header=0, delimiter=',',index_col=0)
        dict_rel = df_rel.T.to_dict('list')
        sourceIP = dict_rel.get(source)[0].split('@')[1]
        destinationIP = dict_rel.get(destination)[0].split('@')[1]
        cursor = self.db['quadratic_parameters'].find({"Source[IP]":sourceIP,"Destination[IP]":destinationIP},{"Parameters":1}).sort([('Time_Stamp[UTC]', -1)]).limit(1)
        try:
            record = cursor.next()
            quadratic = record['Parameters']
            quadratic = quadratic.split(" ")
            quadratic = [float(x) for x in quadratic]
            predicted = np.square(file_size*8)*quadratic[0]+file_size*8*quadratic[1]+quadratic[2]#file_size[Bytes]
        except StopIteration:
            print('No valid links')
            exit()
        return predicted

def main():
    """Load all the confuguration
    """
    HERE     = path.abspath(path.dirname(__file__)) + "/"
    INI_PATH = HERE + 'jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global MONGO_SVC, MONGO_DOCKER

    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])

    if len(sys.argv)<3:
        print('Please run the script as following: python central_query_statistics Source_Tag Destination_Tag FileSize[KB]')
        exit()
    source = sys.argv[1]
    destination = sys.argv[2]
    file_size = int(sys.argv[3])
    d = central_query_statistics()
    predicted = d.do_query_quaratic(source,destination,file_size)
    msg = "Expected latency is %f [ms]" %predicted
    print(msg)
    
if __name__ == '__main__':
    main()

