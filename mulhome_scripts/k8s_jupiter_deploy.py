__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")


import time
import os
from os import path
from multiprocessing import Process
from k8s_profiler_scheduler import *
from k8s_wave_scheduler import *
from k8s_circe_scheduler import *
from k8s_exec_scheduler import *
from k8s_heft_scheduler import *
from pprint import *
import jupiter_config
import requests
import json
from pprint import *
#from utilities import *
import utilities
from k8s_get_service_ips import *
from functools import wraps



def task_mapping_decorator(f):
    """Mapping the chosen scheduling modules based on ``jupiter_config.SCHEDULER`` in ``jupiter_config.ini``
    
    Args:
        f (function): either HEFT or WAVE scheduling modules specified from ``jupiter_config.ini``
    
    Returns:
        function: chosen scheduling modules
    """
    @wraps(f)
    def task_mapping(*args, **kwargs):
      if jupiter_config.SCHEDULER == 0:
        return f(*args, **kwargs)
      else:
        return f(args[0])
    return task_mapping

def empty_function():
    return []

def k8s_jupiter_deploy():
    """
        Deploy all Jupiter components (WAVE, CIRCE, DRUPE) in the system.
    """
    jupiter_config.set_globals()
    
    static_mapping = jupiter_config.STATIC_MAPPING

    if jupiter_config.SCHEDULER == 0: # HEFT
        task_mapping_function  = task_mapping_decorator(k8s_heft_scheduler)
        exec_profiler_function = k8s_exec_scheduler
    else:# WAVE
        task_mapping_function = task_mapping_decorator(k8s_wave_scheduler)
        exec_profiler_function = empty_function

    # This loads the task graph and node list
    if not static_mapping:
        path1 = jupiter_config.APP_PATH + 'configuration.txt'
        path2 = jupiter_config.HERE + 'nodes.txt'

        # start the profilers
        profiler_ips = get_all_profilers()
        #profiler_ips = k8s_profiler_scheduler()


        # start the execution profilers
        execution_ips = get_all_execs()
        #execution_ips = exec_profiler_function()

        print('*************************')
        print('Network Profiling Information:')
        print(profiler_ips)
        print('Execution Profiling Information:')
        print(execution_ips)
        print('*************************')


        node_names = utilities.k8s_get_nodes_string(path2)
        print('*************************')

        #Start the task to node mapper
        task_mapping_function(profiler_ips,execution_ips,node_names)

        """
            Make sure you run kubectl proxy --port=8080 on a terminal.
            Then this is link to get the task to node mapping
        """

        line = "http://localhost:8089/api/v1/namespaces/"
        line = line + jupiter_config.MAPPER_NAMESPACE + "/services/home:" + str(jupiter_config.FLASK_SVC) + "/proxy"
        time.sleep(5)
        print(line)
        while 1:
            try:
                # print("get the data from " + line)
                #time.sleep(5)
                r = requests.get(line)
                mapping = r.json()
                data = json.dumps(mapping)
                # print(mapping)
                # print(len(mapping))
                if len(mapping) != 0:
                    if "status" not in data:
                        break
            except Exception as e:
                print(e)
                print("Will retry to get the mapping!")

        pprint(mapping)
        schedule = utilities.k8s_get_hosts(path1, path2, mapping)
        dag = utilities.k8s_read_dag(path1)
        dag.append(mapping)
        print("Printing DAG:")
        pprint(dag)
        print("Printing schedule")
        pprint(schedule)
        print("End print")

    
    else:
        import static_assignment1 as st
        dag = st.dag
        schedule = st.schedule

    # Start CIRCE
    k8s_circe_scheduler(dag,schedule)

    print("The Jupiter Deployment is Successful!")
    
if __name__ == '__main__':
    k8s_jupiter_deploy()
  
