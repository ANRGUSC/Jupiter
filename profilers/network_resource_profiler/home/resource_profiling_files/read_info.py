'''
 * Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 *     contributor: Pradipta Ghosh, Jiatong Wang, Bhaskar Krishnamachari
 *     Read license file in main directory for more details
'''

import requests
import sys
import json
import time
import datetime
import os
import configparser
from os import path

##
## Load all the confuguration
##
INI_PATH = '/network_profiling/jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])
FLASK_SVC    = int(config['PORT']['FLASK_SVC'])

node_ip = os.environ['SELF_IP']

def open_file():
    list=[]
    ip_path = sys.argv[1]

    with open(ip_path, "r") as ins:
        for line in ins:
            if node_ip == line:
                continue

            line = line.strip('\n')
            print("get the data from http://"+line+ ":" + str(FLASK_SVC))
            r = requests.get("http://"+line+":" + str(FLASK_SVC))
            result = r.json()
            result['ip']=line
            result['last_update']=datetime.datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')
            data=json.dumps(result)
            print(result)
            list.append(data)
        # print list
        return list

