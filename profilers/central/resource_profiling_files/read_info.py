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



def open_file():
    list=[]
    ip_path = sys.argv[1]

    with open(ip_path, "r") as ins:
        for line in ins:
            if node_ip == line:
                continue

            line = line.strip('\n')
            print("get the data from http://"+line+ ":" + str(RP_PORT))
            r = requests.get("http://"+line+":" + str(RP_PORT))
            result = r.json()
            result['ip']=line
            result['last_update']=datetime.datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')
            data=json.dumps(result)
            print(result)
            list.append(data)
        # print list
        return list

if __name__ == '__main__':
    node_ip = os.environ['SELF_IP']
    RP_PORT = 6100