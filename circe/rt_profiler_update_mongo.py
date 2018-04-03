#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Aleksandra Knezevic,Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar, Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import os
import csv
from pymongo import MongoClient
import pandas as pd
import json
import time
from os import path
import configparser

def main():
    """
    This Script Updates the Runtime Profiler data to the mondodb running in the home node. 
    It runs every **5 minute** in this implementation.
    """

    # Load all the confuguration
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    MONGO_PORT  = int(config['PORT']['MONGO_DOCKER'])


    #Update scheduler runtime folder information in mongodb

    while True:
        time.sleep(300)

        client_mongo = MongoClient('mongodb://localhost:' + str(MONGO_PORT) + '/')
        db = client_mongo.central_task_runtime_profiler
        logging = db['droplet_runtime']
        runtime_folder = "/runtime"
        try:
            for subdir, dirs, files in os.walk(runtime_folder):
                for file in files:
                    if file.startswith('.'): continue
                    runtime_file = os.path.join(subdir, file)
                    df = pd.read_csv(runtime_file,delimiter=',',header=None,names = ["Type", "Node IP","Task Name","File Name", "Time","File Size"])
                    data_json = json.loads(df.to_json(orient='records'))
                    logging.insert(data_json)
            print('MongodB Update Successful')
        except Exception as e:
            print('MongoDB error')
            print(e)

if __name__ == '__main__':
    main()