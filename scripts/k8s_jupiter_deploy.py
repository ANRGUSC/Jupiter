"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""
import sys
sys.path.append("../")
import jupiter_config
sys.path.append(jupiter_config.CIRCE_PATH)


import time
import os
from os import path
from multiprocessing import Process
# from readconfig import k8s_read_config, read_config
from k8s_profiler_scheduler import *
from k8s_wave_scheduler import *
from k8s_circe_scheduler import *
from pprint import *
import jupiter_config
import requests
import json
from pprint import *
from utilities import *


static_mapping = False


if __name__ == '__main__':

  if not static_mapping:
    """
        This loads the task graph and node list
    """
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    path2 = jupiter_config.HERE + 'nodes.txt'
    

    # start the profilers
    profiler_ips = k8s_profiler_scheduler()

    # Start the waves
    k8s_wave_scheduler(profiler_ips)

    """
        Make sure you run kubectl proxy --port=8080 on a terminal.
        Then this is link to get the task to node mapping
    """
    line = "http://localhost:8080/api/v1/namespaces/"
    line = line + jupiter_config.WAVE_NAMESPACE + "/services/home:48080/proxy"

    """
      Loop and Sleep until you receive the mapping of the jobs
    """
    time.sleep(5)
    while 1:
        try: 
            # print("get the data from " + line)
            r = requests.get(line)
            mapping = r.json()
            data = json.dumps(mapping)
            # print(mapping)
            # print(len(mapping))
            if len(mapping) != 0:
                if "status" not in data:
                    break
        except:
            print("Some Exception")     

        time.sleep(15)

    # dag_info.append(mapping)

    schedule = k8s_get_hosts(path1, path2, mapping)
    pprint(mapping)
    dag = k8s_read_dag(path1)
    dag.append(mapping)
    print("Printing DAG:")
    pprint(dag)
    print("Printing schedule")
    pprint(schedule)
    print("End print")

    # Use this mapping if you want to bypass the profiler and wave. This will give a static mapping for circe
    # You can then test the coded detectors.
  else:
    import static_assignment
    dag = static_assignment.dag
    schedule = static_assignment.schedule

  # Start CIRCE
  k8s_circe_scheduler(dag,schedule)