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
from k8s_globalinfo_scheduler import *
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
import logging





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
        logging.debug('HEFT mapper')
        return f(*args, **kwargs)
      else: #WAVE
        logging.debug('WAVE mapper')
        return f(args[0],args[3])
    return task_mapping

def setup_port(port):
    """Automatically set up the proxy port
    
    Args:
        port (int): port number
    """
    cmd = "kubectl proxy -p " + str(port) + " &"
    try:
        os.system(cmd)
    except e:
        logging.debug('Error setting up port \n')
        logging.debug(e)

def k8s_jupiter_deploy(app_id,app_name,port):
    """
        Deploy all Jupiter components (WAVE, CIRCE, DRUPE) in the system.
    """
    jupiter_config.set_globals()
    
    static_mapping = jupiter_config.STATIC_MAPPING
    pricing = jupiter_config.PRICING

    if jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3: # HEFT
        logging.debug('Deploy HEFT mapper')
        task_mapping_function  = task_mapping_decorator(k8s_heft_scheduler)
    else:# WAVE
        logging.debug('Deploy WAVE greedy mapper')
        task_mapping_function = task_mapping_decorator(k8s_wave_scheduler)
        

    if jupiter_config.PRICING == 1 or jupiter_config.PRICING == 2:
        logging.debug('Deploy Execution Profiler')
        exec_profiler_function = k8s_exec_scheduler
    elif jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3: # Nonpricing, HEFT
        logging.debug('De[loy Execution Profiler')
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

        logging.debug('*************************')
        logging.debug('Network Profiling Information:')
        logging.debug(profiler_ips)
        logging.debug('Execution Profiling Information:')
        logging.debug(execution_ips)
        logging.debug('*************************')


        logging.debug('******************************')
        logging.debug('Start the global information center')
        k8s_globalinfo_scheduler(app_name)
        
        node_names = utilities.k8s_get_nodes_string(path2)
        logging.debug('*************************')

        #Start the task to node mapper

        if pricing == 0 or  pricing == 1 or pricing == 2 : #original non-pricing
            logging.debug('Start the task to node mapper')
            task_mapping_function(profiler_ips,execution_ips,node_names,app_name)

            """
                Make sure you run kubectl proxy --port=8080 on a terminal.
                Then this is link to get the task to node mapping
            """

            line = "http://localhost:%d/api/v1/namespaces/"%(port)
            line = line + jupiter_config.MAPPER_NAMESPACE + "/services/" +app_name + "-home:" + str(jupiter_config.FLASK_SVC) + "/proxy"
            time.sleep(5)
            logging.debug(line)
            while 1:
                try:
                    logging.debug("get the data from " + line)
                    time.sleep(5)
                    r = requests.get(line)
                    mapping = r.json()
                    data = json.dumps(mapping)
                    logging.debug(data)
                    if len(mapping) != 0:
                        if "status" not in data:
                            break
                except Exception as e:
                    #logging.debug(e)
                    logging.debug("Will retry to get the mapping for app " + app_name)
                    time.sleep(30)


            pprint(mapping)
            schedule = utilities.k8s_get_hosts(path1, path2, mapping)
            logging.debug("Begin logging.debuging schedule")
            pprint(schedule)
            logging.debug("End logging.debuging schedule")
            logging.debug("Begin logging.debuging DAG:")
            dag = utilities.k8s_read_dag(path1)
            pprint(dag)
            dag.append(mapping)
            logging.debug("End logging.debuging DAG")
            pprint(dag)
        else: #integrated_pricing 
            dag = utilities.k8s_read_dag(path1)
            logging.debug("logging.debuging DAG:")
            pprint(dag)
    
    else:
        logging.debug('******************************')
        logging.debug('Start the global information center')
        k8s_globalinfo_scheduler(app_name)
        # import static_assignment_code as st
        import static_assignment_noncode as st
        dag = st.dag
        schedule = st.schedule
        logging.debug('*************************')
        logging.debug('Static schedule information')
        logging.debug('DAG')
        logging.debug(dag)
        logging.debug('schedule')
        logging.debug(schedule)
        logging.debug('*************************')


    # Start CIRCE
    if pricing == 0: #original non-pricing
        logging.debug('Non pricing evaluation')
        k8s_circe_scheduler(dag,schedule,app_name)
    elif pricing == 3: #integrated pricing
        logging.debug('Integrated Pricing evaluation')
        logging.debug(pricing)
        k8s_integrated_pricing_circe_scheduler(dag,profiler_ips,execution_ips,app_name)
    elif pricing == 4: #decoupled pricing
        logging.debug('Decoupled Pricing evaluation')
        logging.debug(pricing)
        k8s_decoupled_pricing_circe_scheduler(dag,profiler_ips,execution_ips,app_name)
        # k8s_decoupled_pricing_circe_scheduler(profiler_ips,app_name)
    else: #event based or push pricing
        logging.debug('Pricing evaluation')
        logging.debug(pricing)
        k8s_pricing_circe_scheduler(dag,schedule,profiler_ips,execution_ips,app_name)


    logging.debug("The Jupiter Deployment is Successful!")


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
    logging.debug('Tear down all current CIRCE deployments')
    if pricing == 0:
        delete_all_circe(app_name)
    else:
        delete_all_pricing_circe(app_name)
    if jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3: # HEFT
        logging.debug('Tear down all current HEFT deployments')
        delete_all_heft(app_name)
        task_mapping_function  = task_mapping_decorator(k8s_heft_scheduler)
    else:# WAVE
        logging.debug('Tear down all current WAVE deployments')
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

        logging.debug('*************************')
        logging.debug('Network Profiling Information2222:')
        logging.debug(profiler_ips)
        logging.debug('Execution Profiling Information:')
        logging.debug(execution_ips)
        logging.debug('*************************')


        node_names = utilities.k8s_get_nodes_string(path2)
        logging.debug('*************************')


        logging.debug('Starting to start HEFT mapping') #all input information was provided
        start_time = time.time()
        #Start the task to node mapper
        task_mapping_function(profiler_ips,execution_ips,node_names,app_name)

        """
            Make sure you run kubectl proxy --port=8080 on a terminal.
            Then this is link to get the task to node mapping
        """

        line = "http://localhost:%d/api/v1/namespaces/"%(port)
        line = line + jupiter_config.MAPPER_NAMESPACE + "/services/"+app_name+"-home:" + str(jupiter_config.FLASK_SVC) + "/proxy"
        time.sleep(5)
        logging.debug(line)
        while 1:
            try:
                logging.debug("get the data from " + line)
                time.sleep(5)
                r = requests.get(line)
                logging.debug(r)
                mapping = r.json()
                logging.debug(mapping)
                data = json.dumps(mapping)
                logging.debug(data)
                # logging.debug(mapping)
                # logging.debug(len(mapping))
                if len(mapping) != 0:
                    if "status" not in data:
                        break
            except:
                logging.debug("Will retry to get the mapping for " + app_name)
                time.sleep(2)
        pprint(mapping)

        logging.debug('Successfully get the mapping')
        end_time = time.time()
        deploy_time = end_time - start_time
        logging.debug('Time to retrive HEFT mapping' + str(deploy_time))

        schedule = utilities.k8s_get_hosts(path1, path2, mapping)
        dag = utilities.k8s_read_dag(path1)
        dag.append(mapping)
        logging.debug("logging.debuging DAG:")
        pprint(dag)
        logging.debug("logging.debuging schedule")
        pprint(schedule)
        logging.debug("End logging.debug")

    
    else:
        import static_assignment_noncode
        # dag = static_assignment.dag
        # schedule = static_assignment.schedule

    logging.debug('Network Profiling Information:')
    logging.debug(profiler_ips)
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
    line = line + jupiter_config.DEPLOYMENT_NAMESPACE + "/services/" + app_name+ "-home:" + str(jupiter_config.FLASK_SVC) + "/proxy"
    logging.debug('Check if finishing evaluation sample tests')
    logging.debug(line)
    while 1:
        try:
            logging.debug("Number of output files for app: " + app_name)
            r = requests.get(line)
            num_files = r.json()
            data = int(json.dumps(num_files))
            logging.debug(data)
            logging.debug(num_samples)
            if data == num_samples:
                logging.debug('Finish running all sample files!!!!!!!!')
                break
            time.sleep(60)
        except Exception as e: 
            logging.debug(e)
            logging.debug("Will check back later if finishing all the samples for app " + app_name)
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
        logging.debug('Finish one run !!!!!!!!!!!!!!!!!!!!!!')
        t = str(datetime.datetime.now())
        logging.debug(t)            
        time.sleep(30)
        # redeploy_system(app_id,app_name,port)
    #teardown_system(app_name)
    
def main():
    """ 
        Deploy num_dags of the application specified by app_name
    """

    global logging
    logging.basicConfig(level = logging.DEBUG)
    
    jupiter_config.set_globals()
    app_name = jupiter_config.APP_OPTION
    circe_port = int(jupiter_config.FLASK_CIRCE)
    flask_deploy = int(jupiter_config.FLASK_DEPLOY )
    
    num_samples_files = 300
    num_runs = 1
    num_dags_list = [1]
    #num_dags_list = [1,2,4,6,8,10]
    for num_dags in num_dags_list:
        temp = app_name
        logging.debug(num_dags)
        jupiter_config.set_globals()
        port_list = []
        app_list = []
        for num in range(1,num_dags + 1):
            port =  circe_port + num - 1
            cur_app = temp + str(num)
            port_list.append(port)
            app_list.append(cur_app)     
        logging.debug(port_list)
        logging.debug(app_list)
       
        for idx,appname in enumerate(app_list):
            logging.debug(appname)
            _thread.start_new_thread(deploy_app_jupiter, (app_name,appname,port_list[idx],num_runs,num_samples_files))

    app.run(host='0.0.0.0', port = flask_deploy)
if __name__ == '__main__':
    main()
