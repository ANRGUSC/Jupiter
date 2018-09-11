__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
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
from delete_all_waves import *
from delete_all_heft import *

from flask import Flask, request
from k8s_jupiter_deploy import *
import datetime

from k8s_get_service_ips import *
from functools import wraps
import _thread




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
      if jupiter_config.SCHEDULER == 0:
        return f(*args, **kwargs)
      else:
        return f(args[0])
    return task_mapping

def empty_function():
    return []

def setup_port(port):
    cmd = "kubectl proxy -p " + str(port)+ " &"
    try:
        os.system(cmd)
    except e:
        print('Error setting up port \n')
        print(e)

def k8s_jupiter_deploy(port,app_name):
    """
        Deploy all Jupiter components (WAVE, CIRCE, DRUPE) in the system.
    """
    jupiter_config.set_globals()
    
    static_mapping = jupiter_config.STATIC_MAPPING
    pricing = jupiter_config.PRICING


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
                # print("get the data from " + line)
                #time.sleep(5)
                r = requests.get(line)
                mapping = r.json()
                data = json.dumps(mapping)
                if len(mapping) != 0:
                    if "status" not in data:
                        break
            except Exception as e:
                #print(e)
                print("Will retry to get the mapping for app "+ app_name)
                time.sleep(30)


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
    if pricing == 0:
    	k8s_circe_scheduler(dag,schedule,app_name)
    else:
    	k8s_pricing_circe_scheduler(dag,schedule,profiler_ips,execution_ips,app_name)


    print("The Jupiter Deployment is Successful!")

def get_pod_logs(namespace, pod_name, log_name):
    """Generate log of pod given name space and pod name
    
    Args:
        namespace (str): corresponding name space
        pod_name (str): corresponding pod name
    """
    ts = int(time.time())
    log_file = "%s_%d.log" %(log_name,ts)
    bash_log = "kubectl logs %s -n %s > %s"%(pod_name,namespace,log_file)
    os.system(bash_log)
    # log_runtime = "../logs/original_greedy_both_dummy_runtime_%d.log" %(ts)
    # bash_runtime = "kubectl cp %s/%s:runtime_tasks.txt %s "%(namespace,pod_name,log_runtime)
    # os.system(bash_runtime)


def export_circe_log(app_name,log_name):
    """Export circe home log for evaluation, should only use when for non-static mapping
    """
    jupiter_config.set_globals()
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = utilities.k8s_read_dag(path1)
    dag = dag_info[1]
    print(dag)
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    core_v1_api = client.CoreV1Api()
    resp = core_v1_api.list_namespaced_pod(jupiter_config.DEPLOYMENT_NAMESPACE)
    home_name=app_name+'-home'
    for i in resp.items:
        if i.metadata.name.startswith(home_name):
            circe_name = i.metadata.name
            break;
    print('******************* Circe pod to export')
    print(circe_name)
    get_pod_logs(jupiter_config.DEPLOYMENT_NAMESPACE,circe_name,log_name)



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
        return f(args[0],args[3])
    return task_mapping

def empty_function():
    return []



def redeploy_system(app_name,port):
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
    delete_all_circe()
    if jupiter_config.SCHEDULER == 0: # HEFT
        print('Tear down all current HEFT deployments')
        delete_all_heft()
        task_mapping_function  = task_mapping_decorator(k8s_heft_scheduler)
        exec_profiler_function = k8s_exec_scheduler
    else:# WAVE
        print('Tear down all current WAVE deployments')
        delete_all_waves()
        task_mapping_function = task_mapping_decorator(k8s_wave_scheduler)
        exec_profiler_function = empty_function

    # This loads the task graph and node list
    if not static_mapping:
        path1 = jupiter_config.APP_PATH + 'configuration.txt'
        path2 = jupiter_config.HERE + 'nodes.txt'

        # start the profilers
        profiler_ips = get_all_profilers()
        # profiler_ips = k8s_profiler_scheduler()


        # start the execution profilers
        execution_ips = get_all_execs()
        # execution_ips = exec_profiler_function()

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
                print("Will retry to get the mapping for " + app_name)
                time.sleep(30)
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
        import static_assignment
        # dag = static_assignment.dag
        # schedule = static_assignment.schedule

    # Start CIRCE
    if pricing == 0:
    	k8s_circe_scheduler(dag,schedule,app_name)
    else:
    	k8s_pricing_circe_scheduler(dag,schedule,profiler_ips,execution_ips,app_name)



def check_finish_evaluation(app_name,port,num_samples):
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
            #print(e)
            print("Will check back later if finishing all the samples for app "+app_name)
            time.sleep(60)

   
def deploy_app_jupiter(app_name,port,log,num_runs,num_samples):
    setup_port(port)
    k8s_jupiter_deploy(port,app_name)
    log_name = "../logs/evaluation_log_" + app_name+":"+str(port) 
    with open(log_name,'w+') as f:
        for i in range(0,num_runs):
            file_log = log+'_'+str(i)
            f.write('============================\n')
            check_finish_evaluation(app_name,port,num_samples)
            f.write('\nFinish one run !!!!!!!!!!!!!!!!!!!!!!')
            t = str(datetime.datetime.now())
            print(t)            
            f.write(t)
            f.write('\nExport the log for this run')
            export_circe_log(app_name,file_log)
            time.sleep(30)
            f.write('\nRedeploy the system')
            redeploy_system(app_name,port)
        f.write('\nFinish the experiments for the current application')
    
def main():
    """ 
        Deploy num_dags of the application specified by app_name
    """
    app_name = 'dummy'
    num_samples = 2
    num_runs = 2
    num_dags = 1
    jupiter_config.set_globals()
    if jupiter_config.SCHEDULER == 0:
        alg = 'heft'
    elif jupiter_config.SCHEDULER == 1:
        alg = 'random'
    else:
        alg = 'greedy'
    
    port_list = []
    app_list = []
    log_list = []
    for num in range(1,num_dags+1):
        log_name = '../logs/%s_DAG%d_%dRUN_circehome' %(alg,num,num_runs)
        port =  8080 + num-1
        cur_app = app_name+str(num)
        port_list.append(port)
        app_list.append(cur_app)
        log_list.append(log_name)        
    print(port_list)
    print(app_list)
    print(log_list)
   
    for idx,app_name in enumerate(app_list):
        _thread.start_new_thread(deploy_app_jupiter, (app_name,port_list[idx],log_list[idx],num_runs,num_samples))



    app.run(host='0.0.0.0', port=int(jupiter_config.FLASK_DOCKER))
if __name__ == '__main__':
    main()
