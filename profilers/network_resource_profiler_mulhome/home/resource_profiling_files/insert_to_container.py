
__author__ = "Jiatong Wang, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

from pymongo import MongoClient
import sys
import read_info
import configparser
from os import path



def insert_data(res):
    """Insert resource information(CPU and Memory usage information) in the ``central_resource_profiler`` Mongo database
    
    Args:
        res (list): node list read from node file
    """

    try:
        Client = MongoClient('mongodb://localhost:' + str(MONGO_DOCKER) + '/')

        db = Client["central_resource_profiler"]

        coll = db["resource_info"]
        for i in res:
            info = eval(i)
            key_to_check = {'ip':info['ip']}
            coll.update(key_to_check,info,upsert=True)  

        print("insert successfully")
    except Exception as e:
        print("data insertion failed. details: " + str(e))
        
def main():
    """
        - Load all the configuration
        - Get node list file path from environment variable
        - Get resource profiling information for all the nodes in the node file
        - Insert resource profiling information to ``central_resource_profiler`` database 
    """

    INI_PATH = '/network_profiling/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global MONGO_SVC, MONGO_DOCKER, ip_path

    MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
    MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])

    if  len(sys.argv)!=2:
        print("Usage:python3 insert_to_container.py ip_file")
        sys.exit(2)

    print('**********************************2')
    ip_path = sys.argv[1]
    print(ip_path)
    res=read_info.open_file()
    print(res)
    insert_data(res)

if __name__ == '__main__':
    main()    
