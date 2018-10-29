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
from delete_all_pricing_circe import *
from delete_all_waves import *
from delete_all_heft import *
from auto_teardown_system import *

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

def k8s_jupiter_deploy(app_id,app_name,port,mapper_log):
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
                if len(mapping) != 0:
                    if "status" not in data:
                        break
            except Exception as e:
                #print(e)
                print("Will retry to get the mapping for app "+ app_name)
                time.sleep(30)


        pprint(mapping)
        export_mapper_log(app_name,mapper_log)
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

def get_pod_logs_circe(namespace, pod_name, log_name):
    """Generate log of pod given name space and pod name
    
    Args:
        namespace (str): corresponding name space
        pod_name (str): corresponding pod name
    """
    print('^^^^^^^^^^^^^^^^^^^^^^^^^^^')
    print(namespace)
    print(pod_name)
    print(log_name)
    ts = int(time.time())
    log_file = "%s_%d.log" %(log_name,ts)
    bash_log = "kubectl logs %s -n %s > %s"%(pod_name,namespace,log_file)
    os.system(bash_log)


    log_runtime = "../logs/%s_runtime_%d.log" %(log_name,ts)
    bash_runtime = "kubectl cp %s/%s:runtime_tasks.txt %s "%(namespace,pod_name,log_runtime)
    print(bash_runtime)
    os.system(bash_runtime)

    log_send = "../logs/%s_sender_%d.log" %(log_name,ts)
    bash_send = "kubectl cp %s/%s:runtime_transfer_sender.txt %s "%(namespace,pod_name,log_send)
    print(bash_send)
    os.system(bash_send)

    log_receive = "../logs/%s_receiver_%d.log" %(log_name,ts)
    bash_receive = "kubectl cp %s/%s:runtime_transfer_receiver.txt %s "%(namespace,pod_name,log_receive)
    os.system(bash_receive)

def get_pod_logs_mapper(namespace, pod_name, log_name):
    """Generate log of pod given name space and pod name
    
    Args:
        namespace (str): corresponding name space
        pod_name (str): corresponding pod name
    """
    print('^^^^^^^^^^^^^^^^^^^^^^^^^^^')
    print(namespace)
    print(pod_name)
    print(log_name)
    ts = int(time.time())
    log_file = "%s_%d.log" %(log_name,ts)
    bash_log = "kubectl logs %s -n %s > %s"%(pod_name,namespace,log_file)
    os.system(bash_log)



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
    get_pod_logs_circe(jupiter_config.DEPLOYMENT_NAMESPACE,circe_name,log_name)


def export_mapper_log(app_name,log_name):
    """Export circe home log for evaluation, should only use when for non-static mapping
    """
    jupiter_config.set_globals()
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    core_v1_api = client.CoreV1Api()
    resp = core_v1_api.list_namespaced_pod(jupiter_config.MAPPER_NAMESPACE)
    home_name=app_name+'-home'
    for i in resp.items:
        if i.metadata.name.startswith(home_name):
            mapper_name = i.metadata.name
            break;
    print('******************* Mapper pod to export')
    print(mapper_name)
    get_pod_logs_mapper(jupiter_config.MAPPER_NAMESPACE,mapper_name,log_name)



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



def redeploy_system(app_id,app_name,port,mapper_log):
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
    if jupiter_config.SCHEDULER == 0: # HEFT
        print('Tear down all current HEFT deployments')
        delete_all_heft(app_name)
        task_mapping_function  = task_mapping_decorator(k8s_heft_scheduler)
        exec_profiler_function = k8s_exec_scheduler
    else:# WAVE
        print('Tear down all current WAVE deployments')
        delete_all_waves(app_name)
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
        execution_ips = get_all_execs(app_id)
        # execution_ips = exec_profiler_function()

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

        export_mapper_log(app_name,mapper_log)
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

    print('Network Profiling Information2222:')
    print(profiler_ips)
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

   
def deploy_app_jupiter(app_id,app_name,port,circe_log,num_runs,num_samples,mapper_log):
    setup_port(port)
    k8s_jupiter_deploy(app_id,app_name,port,mapper_log)
    log_folder ='../logs'
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    log_name = "../logs/evaluation_log_" + app_name+":"+str(port) 
    with open(log_name,'w+') as f:
        for i in range(0,num_runs):
            file_log = circe_log+'_'+str(i)
            f.write('============================\n')
            check_finish_evaluation(app_name,port,num_samples)
            f.write('\nFinish one run !!!!!!!!!!!!!!!!!!!!!!')
            t = str(datetime.datetime.now())
            print(t)            
            f.write(t)
            f.write('\nExport the log for this run')
            export_circe_log(app_name,file_log)
            time.sleep(30)
            # f.write('\nRedeploy the system')
            # redeploy_system(app_id,app_name,port,mapper_log)
        f.write('\nFinish the experiments for the current application')
    #teardown_system(app_name)
    
def main():
    """ 
        Deploy num_dags of the application specified by app_name
    """
    app_name = 'dummy'
    num_samples = 2
    num_runs = 1
    num_dags_list = [1]
    #num_dags_list = [1,2,4,6,8,10]
    for num_dags in num_dags_list:
        temp = app_name
        print(num_dags)
        jupiter_config.set_globals()
        if jupiter_config.SCHEDULER == 0:
            alg = 'heft'
        elif jupiter_config.SCHEDULER == 1:
            alg = 'random'
        else:
            alg = 'greedy'
        
        if jupiter_config.PRICING == 1:
            option = 'pricing'
        else:
            option = 'nopricing'
        port_list = []
        app_list = []
        log_circe_list = []
        log_mapper_list = []
        for num in range(1,num_dags+1):
            log_circe = '../logs/%s_%s_%dDAG%d_%dRUN_circehome' %(option, alg,num_dags,num,num_runs)
            log_mapper = '../logs/%s_%s_%dDAG%d_%dRUN_mapperhome' %(option, alg,num_dags,num,num_runs)
            port =  8088 + num-1
            cur_app = temp+str(num)
            port_list.append(port)
            app_list.append(cur_app)
            log_circe_list.append(log_circe)  
            log_mapper_list.append(log_mapper)       
        print(port_list)
        print(app_list)
        print(log_circe_list)
       
        for idx,appname in enumerate(app_list):
            print(appname)
            _thread.start_new_thread(deploy_app_jupiter, (app_name,appname,port_list[idx],log_circe_list[idx],num_runs,num_samples,log_mapper_list[idx]))



    app.run(host='0.0.0.0')
if __name__ == '__main__':
    main()
