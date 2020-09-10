__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
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
from k8s_pricing_circe_scheduler import *
from k8s_exec_scheduler import *
from k8s_heft_scheduler import *
from pprint import *
import jupiter_config
import requests
import json
from pprint import *
import utilities
from k8s_get_service_ips import *
from functools import wraps
from delete_all_circe import *
from delete_all_pricing_circe import *
from delete_all_waves import *
from delete_all_heft import *
from auto_teardown_system import *

from flask import Flask, request
import datetime

from functools import wraps
import _thread
import cProfile
import configparser





app = Flask(__name__)

def task_mapping_decorator(f):
    """Mapping the chosen scheduling modules based on ``jupiter_config.SCHEDULER`` in ``jupiter_config.ini``
    
    Args:
        f (function): either HEFT or WAVE scheduling modules specified from ``jupiter_config.ini``
    
    Returns:
        function: chosen scheduling modules
    """
    @wraps(f)
    def task_mapping(*args, **kwargs):
      if jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3: #HEFT
        print('HEFT mapper')
        return f(*args, **kwargs)
      else: #WAVE
        print('WAVE mapper')
        return f(args[0],args[3])
    return task_mapping
        
def setup_port(port):
    """Automatically set up the proxy port
    
    Args:
        port (int): port number
    """
    cmd = "kubectl proxy -p " + str(port)+ " &"
    try:
        os.system(cmd)
    except e:
        print('Error setting up port \n')
        print(e)

def k8s_jupiter_deploy(app_id,app_name,port):
    """
        Deploy all Jupiter components (WAVE, CIRCE, DRUPE) in the system.
    """
    jupiter_config.set_globals()
    
    static_mapping = jupiter_config.STATIC_MAPPING
    pricing = jupiter_config.PRICING

    if jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3: # HEFT
        print('Deploy HEFT mapper')
        task_mapping_function  = task_mapping_decorator(k8s_heft_scheduler)
    else:# WAVE
        print('Deploy WAVE greedy mapper')
        task_mapping_function = task_mapping_decorator(k8s_wave_scheduler)
        

    if jupiter_config.PRICING == 1 or jupiter_config.PRICING == 2:
        print('Deploy Execution Profiler')
        exec_profiler_function = k8s_exec_scheduler
    elif jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3: # Nonpricing, HEFT
        print('Deploy Execution Profiler')
        exec_profiler_function = k8s_exec_scheduler
    else: # Nonpricing, WAVE
        exec_profiler_function = empty_function


    # This loads the task graph and node list
    if not static_mapping:
        path1 = 'new_dag.txt'
        path2 = jupiter_config.HERE + 'nodes.txt'

        # start the profilers
        profiler_ips = get_all_profilers()
        #profiler_ips = k8s_profiler_scheduler()


        # start the execution profilers
        execution_ips = get_all_execs(app_id)
        #execution_ips = exec_profiler_function(app_id)

        print('*************************')
        print('Network Profiling Information:')
        print(profiler_ips)
        print('Execution Profiling Information:')
        print(execution_ips)
        print('*************************')


        node_names = utilities.k8s_get_nodes_string(path2)
        print('*************************')

        #Start the task to node mapper
        
        task_mapping_function(profiler_ips,execution_ips,node_names,app_name)

        """
            Make sure you run kubectl proxy --port=8080 on a terminal.
            Then this is link to get the task to node mapping
        """

        line = "http://localhost:%d/api/v1/namespaces/"%(port)
        line = line + jupiter_config.MAPPER_NAMESPACE + "/services/"+app_name+"-home:" + str(jupiter_config.FLASK_SVC) + "/proxy"
        time.sleep(5)
        print(line)
        while 1:
            try:
                print("get the data from " + line)
                time.sleep(5)
                r = requests.get(line)
                mapping = r.json()
                data = json.dumps(mapping)
                print(data)
                if len(mapping) != 0:
                    if "status" not in data:
                        break
            except Exception as e:
                #print(e)
                print("Will retry to get the mapping for app "+ app_name)
                time.sleep(30)

        """
        for duplication: example mapping sent from scheduler
        {'task0': 'node3', 'task1': 'node4', 'task2': 'node15', 'task3': 'node6', 
         'UPDATED_DAG_FILE_WITH_DUPICATION': 
         '15\ntask0 1 true task1 task2 task2-dup task2-dup task2-dup task2-dup task2-dup task2-dup task2-dup task2-dup task2-dup\ntask1 1 true task3\ntask2 1 true\ntask3 2 true home\ntask2-dup 1 true task3\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask0-dup 1 true task2-dup\n', 
         'task2-dup': 'node14', 
         'task0-dup': 'node13'}

        """
        dag_str = mapping['UPDATED_DAG_FILE_WITH_DUPICATION']
        del mapping['UPDATED_DAG_FILE_WITH_DUPICATION']
        print(dag_str)
        f = open(path1, "w")
        f.write(dag_str)
        f.close()
        schedule = utilities.k8s_get_hosts(path1, path2, mapping)
        dag = utilities.k8s_read_dag(path1)
        dag.append(mapping)
        print("Printing DAG:")
        pprint(dag)
        print("Printing schedule")
        pprint(schedule)
        print("End print")
        
        pprint(mapping)
        schedule = utilities.k8s_get_hosts(path1, path2, mapping)
        dag = utilities.k8s_read_dag(path1)
        dag.append(mapping)
        """
        Example output:
        Printing DAG:
        ['task0',
         {'task0': ['1', 'true', 'task1', 'task2'],
          'task1': ['1', 'true', 'task3'],
          'task2': ['1', 'true', 'task3'],
          'task3': ['2', 'true', 'home']},
         {'task0': ['node1',
                    0.16960351262061335,
                    'node3',
                    0.4178843543834354,
                    'node5',
                    0.41251213299595124],
          'task1': ['node2', 0.7290640758913959, 'node7', 0.2709359241086041],
          'task2': 'node6',
          'task3': 'node4'}]
          
        Printing schedule
        ['task0',
         {'task0': ['1', 'true', 'task1', 'task2'],
          'task1': ['1', 'true', 'task3'],
          'task2': ['1', 'true', 'task3'],
          'task3': ['2', 'true', 'home']},
         {'home': ['home', 'ubuntu-s-2vcpu-4gb-sfo2-01'],
          'task0': ['task0',
                    'ubuntu-s-1vcpu-2gb-nyc3-01',
                    'task0',
                    'ubuntu-s-1vcpu-2gb-sfo2-03',
                    'task0',
                    'ubuntu-s-1vcpu-2gb-sfo2-01'],
          'task1': ['task1',
                    'ubuntu-s-1vcpu-2gb-nyc3-02',
                    'task1',
                    'ubuntu-s-1vcpu-2gb-sfo2-02'],
          'task2': ['task2', 'ubuntu-s-1vcpu-2gb-sfo2-04'],
          'task3': ['task3', 'ubuntu-s-1vcpu-2gb-sfo2-05']},
          {NODES}]
        End print
        """
        print("Printing DAG:")
        pprint(dag)
        print("Printing schedule")
        pprint(schedule)
        print("End print")
        
    
    else:
        import static_assignment1 as st
        dag = st.dag
        schedule = st.schedule

    #Start CIRCE
    if pricing == 0:
        print('Non pricing evaluation')
        k8s_circe_scheduler(dag,schedule,app_name)
    else:
        print('Pricing evaluation')
        print(pricing)
        k8s_pricing_circe_scheduler(dag,schedule,profiler_ips,execution_ips,app_name)


    print("The Jupiter Deployment is Successful!")


def empty_function(app_id):
    """Empty function
    
    Args:
        app_id (str): application id
    
    """
    return []



def redeploy_system(app_id,app_name,port):
    """
        Redeploy the whole system
    """
    jupiter_config.set_globals()
    
    static_mapping = jupiter_config.STATIC_MAPPING
    pricing = jupiter_config.PRICING
    
    """
        Tear down all current deployments
    """
    print('Tear down all current CIRCE deployments')
    if pricing == 0:
        delete_all_circe(app_name)
    else:
        delete_all_pricing_circe(app_name)
    if jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3: # HEFT
        print('Tear down all current HEFT deployments')
        delete_all_heft(app_name)
        task_mapping_function  = task_mapping_decorator(k8s_heft_scheduler)
    else:# WAVE
        print('Tear down all current WAVE deployments')
        delete_all_waves(app_name)
        task_mapping_function = task_mapping_decorator(k8s_wave_scheduler)
        

    if jupiter_config.PRICING == 1 or jupiter_config.PRICING == 2:
        exec_profiler_function = k8s_exec_scheduler
    elif jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3: # Nonpricing, HEFT
        exec_profiler_function = k8s_exec_scheduler
    else: # Nonpricing, WAVE
        exec_profiler_function = empty_function
        
        
    # This loads the task graph and node list
    if not static_mapping:
        path1 = jupiter_config.APP_PATH + 'configuration.txt'
        path2 = jupiter_config.HERE + 'nodes.txt'

        # start the profilers
        profiler_ips = get_all_profilers()
        #profiler_ips = k8s_profiler_scheduler()


        # start the execution profilers
        execution_ips = get_all_execs(app_id)
        #execution_ips = exec_profiler_function(app_id)

        print('*************************')
        print('Network Profiling Information2222:')
        print(profiler_ips)
        print('Execution Profiling Information:')
        print(execution_ips)
        print('*************************')


        node_names = utilities.k8s_get_nodes_string(path2)
        print('*************************')


        #Start the task to node mapper
        task_mapping_function(profiler_ips,execution_ips,node_names,app_name)

        """
            Make sure you run kubectl proxy --port=8080 on a terminal.
            Then this is link to get the task to node mapping
        """

        line = "http://localhost:%d/api/v1/namespaces/"%(port)
        line = line + jupiter_config.MAPPER_NAMESPACE + "/services/"+app_name+"-home:" + str(jupiter_config.FLASK_SVC) + "/proxy"
        time.sleep(5)
        print(line)
        while 1:
            try:
                print("get the data from " + line)
                time.sleep(5)
                r = requests.get(line)
                print(r)
                mapping = r.json()
                print(mapping)
                data = json.dumps(mapping)
                print(data)
                # print(mapping)
                # print(len(mapping))
                if len(mapping) != 0:
                    if "status" not in data:
                        break
            except:
                print("Will retry to get the mapping for " + app_name)
                time.sleep(30)
        pprint(mapping)

        """
        for duplication: example mapping sent from scheduler
        {'task0': 'node3', 'task1': 'node4', 'task2': 'node15', 'task3': 'node6', 
         'UPDATED_DAG_FILE_WITH_DUPICATION': 
         '15\ntask0 1 true task1 task2 task2-dup task2-dup task2-dup task2-dup task2-dup task2-dup task2-dup task2-dup task2-dup\ntask1 1 true task3\ntask2 1 true\ntask3 2 true home\ntask2-dup 1 true task3\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask2-dup 1 true\ntask0-dup 1 true task2-dup\n', 
         'task2-dup': 'node14', 
         'task0-dup': 'node13'}

        """
        dag_str = mapping['UPDATED_DAG_FILE_WITH_DUPICATION']
        del mapping['UPDATED_DAG_FILE_WITH_DUPICATION']
        #rewrite_graph_file(path1, dag_str)
        schedule = utilities.k8s_get_hosts(path1, path2, mapping)
        dag = utilities.k8s_read_dag(path1)
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

    print('Network Profiling Information:')
    print(profiler_ips)
    # Start CIRCE
    if pricing == 0:
        k8s_circe_scheduler(dag,schedule,app_name)
    else:
        k8s_pricing_circe_scheduler(dag,schedule,profiler_ips,execution_ips,app_name)


def check_finish_evaluation(app_name,port,num_samples):
    """Check if the evaluation script is finished
    
    Args:
        app_name (str): application name
        port (int): port number 
        num_samples (int): number of sample files
    """
    jupiter_config.set_globals()
    line = "http://localhost:%d/api/v1/namespaces/"%(port)
    line = line + jupiter_config.DEPLOYMENT_NAMESPACE + "/services/"+app_name+"-home:" + str(jupiter_config.FLASK_SVC) + "/proxy"
    print('Check if finishing evaluation sample tests')
    print(line)
    while 1:
        try:
            print("Number of output files :")
            r = requests.get(line)
            num_files = r.json()
            data = int(json.dumps(num_files))
            print(data)
            print(num_samples)
            if data==num_samples:
                print('Finish running all sample files!!!!!!!!')
                break
            time.sleep(60)
        except Exception as e: 
            print(e)
            print("Will check back later if finishing all the samples for app "+app_name)
            time.sleep(60)

   
def deploy_app_jupiter(app_id,app_name,port,num_runs,num_samples):
    """Deploy JUPITER given all the input parameters
    
    Args:
        app_id (str): Application ID
        app_name (str): Application name
        port (int): port number
        num_runs (int): number of runs
        num_samples (int): number of samples
    """
    setup_port(port)
    k8s_jupiter_deploy(app_id,app_name,port)
    for i in range(0,num_runs):
        check_finish_evaluation(app_name,port,num_samples)
        print('Finish one run !!!!!!!!!!!!!!!!!!!!!!')
        t = str(datetime.datetime.now())
        print(t)            
        time.sleep(30)
        # redeploy_system(app_id,app_name,port)
    #teardown_system(app_name)
    
def main():
    """ 
        Deploy num_dags of the application specified by app_name
    """
    
    jupiter_config.set_globals()
    app_name = jupiter_config.APP_OPTION
    circe_port = int(jupiter_config.FLASK_CIRCE)
    
    
    num_samples = 2
    num_runs = 1
    num_dags_list = [1]
    #num_dags_list = [1,2,4,6,8,10]
    for num_dags in num_dags_list:
        temp = app_name
        print(num_dags)
        jupiter_config.set_globals()
        port_list = []
        app_list = []
        for num in range(1,num_dags+1):
            port =  circe_port + num-1
            cur_app = temp+str(num)
            port_list.append(port)
            app_list.append(cur_app)     
        print(port_list)
        print(app_list)
       
        for idx,appname in enumerate(app_list):
            print(appname)
            _thread.start_new_thread(deploy_app_jupiter, (app_name,appname,port_list[idx],num_runs,num_samples))
    app.run(host='0.0.0.0',port='5555')
if __name__ == '__main__':
    main()
