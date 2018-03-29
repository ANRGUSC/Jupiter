__author__ = "Pradipta Ghosh, Pranav Sakulkar, Jason A Tran, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

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
from utilities import *
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

def main():
    """
        Deploy all Jupiter components (WAVE, CIRCE, DRUPE) in the system.
    """
    import jupiter_config
    
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
        # profiler_ips = get_all_profilers()
        profiler_ips = k8s_profiler_scheduler()


        # start the execution profilers
        # execution_ips = get_all_execs()
        execution_ips = exec_profiler_function()

        print('*************************')
        print('Network Profiling Information:')
        print(profiler_ips)
        print('Execution Profiling Information:')
        print(execution_ips)
        print('*************************')


        node_names = k8s_get_nodes_string(path2)
        print('*************************')

        #Start the task to node mapper
        task_mapping_function(profiler_ips,execution_ips,node_names)

        """
            Make sure you run kubectl proxy --port=8080 on a terminal.
            Then this is link to get the task to node mapping
        """

        line = "http://localhost:8080/api/v1/namespaces/"
        line = line + jupiter_config.MAPPER_NAMESPACE + "/services/home:" + str(jupiter_config.FLASK_SVC) + "/proxy"
        time.sleep(5)
        print(line)
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
        pprint(mapping)
        schedule = k8s_get_hosts(path1, path2, mapping)
        dag = k8s_read_dag(path1)
        dag.append(mapping)
        print("Printing DAG:")
        pprint(dag)
        print("Printing schedule")
        pprint(schedule)
        print("End print")

    
    else:
        import static_assignment
        # dag = static_assignment.dag
        # schedule = static_assignment.schedule

    # Start CIRCE
    k8s_circe_scheduler(dag,schedule)

if __name__ == '__main__':
    main()
  