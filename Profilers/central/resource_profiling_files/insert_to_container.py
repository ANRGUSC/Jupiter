'''
 * Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 *     contributor: Pradipta Ghosh, Jiatong Wang, Bhaskar Krishnamachari
 *     Read license file in main directory for more details
'''

from pymongo import MongoClient
import sys
import read_info

def insert_data(res):


    Client = MongoClient("mongodb://localhost:27017/")

    db = Client["central_resource_profiler"]

    coll = db["resource_info"]
    for i in res:
        info = eval(i)
        key_to_check = {'ip':info['ip']}
        coll.update(key_to_check,info,upsert=True)  

    print("insert successfully")


if __name__ == '__main__':
    if  len(sys.argv)!=2:
        print("Usage:python3 insert_to_container.py ip_file")
        sys.exit(2)
    ip_path = sys.argv[1]
    res=read_info.open_file()
    insert_data(res)
