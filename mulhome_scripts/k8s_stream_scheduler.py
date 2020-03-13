__author__ = "Quynh Nguyen, Pradipta Ghosh and  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "4.0"

import sys
sys.path.append("../../")

import time
import os
from os import path
from multiprocessing import Process
from write_stream_service_specs import *
from write_stream_specs import *
import yaml
from kubernetes import client, config
from pprint import *
import jupiter_config
import utilities
from kubernetes.client.rest import ApiException

def get_service_circe(dag,app_name):
    jupiter_config.set_globals()
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE
    api = client.CoreV1Api()

    service_ips = {}
    home_name =app_name+"-home"
    try:
        resp = api.read_namespaced_service(home_name, namespace)
        service_ips['home'] = resp.spec.cluster_ip
    except ApiException as e:
        print(e)
        print("Exception Occurred")

    for key, value in dag.items():
        task = key
        nexthosts = ''
 
        """
            Generate the yaml description of the required service for each task
        """
        pod_name = app_name+"-"+task
        try:
            resp = api.read_namespaced_service(pod_name, namespace)
            service_ips[task] = resp.spec.cluster_ip
        except ApiException as e:
            print(e)
            print("Exception Occurred")
    return service_ips




def k8s_stream_scheduler(app_name):
    """
        This script deploys CIRCE in the system. 
    """
    

    jupiter_config.set_globals()
    
    sys.path.append(jupiter_config.STREAM_PATH)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    
    """
        We have defined the namespace for deployments in jupiter_config
    """
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE
    
    """
        Get proper handles or pointers to the k8-python tool to call different functions.
    """
    api = client.CoreV1Api()
    k8s_beta = client.ExtensionsV1beta1Api()

    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = utilities.k8s_read_dag(path1)
    #get DAG and home machine info
    first_task = dag_info[0]
    dag = dag_info[1]
    
    print('DAG info:')
    print(dag)

    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes,datasources = utilities.k8s_get_all_elements(path2)

    service_ips = {}; #list of all service IPs
    
    for i in datasources:
        print('Data source information')
        print('First create the home node service')
        home_name =app_name+"-stream"+i
        home_body = write_stream_service_specs(name = home_name)
        
        try:
            ser_resp = api.create_namespaced_service(namespace, home_body)
            print("Home service created. status = '%s'" % str(ser_resp.status))
            resp = api.read_namespaced_service(home_name, namespace)
            service_ips['home'] = resp.spec.cluster_ip
        except ApiException as e:
            print(e)
            print("Exception Occurred")

    circe_services = get_service_circe(dag,app_name)
    circe_nodes = ' '.join(circe_services.keys())
    circe_nodes_ips = ' '.join(circe_services.values())
    
    for i in datasources:
        
        home_name =app_name+"-stream"+i

        home_dep = write_stream_home_specs(name=home_name,image = jupiter_config.STREAM_IMAGE, 
                                    host = jupiter_config.STREAM_NODE[i][0], 
                                    child = jupiter_config.HOME_CHILD,
                                    child_ips = circe_services.get(jupiter_config.HOME_CHILD), 
                                    appname = app_name,
                                    appoption = jupiter_config.APP_OPTION,
                                    dir = '{}',
                                    self_name=i,
                                    home_node_ip = circe_services.get('home'),
                                    all_nodes = circe_nodes,
                                    all_nodes_ips = circe_nodes_ips)

        try:
            resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
            print("Home deployment created")
            print("Home deployment created. status = '%s'" % str(resp.status))
        except ApiException as e:
            print(e)

   
if __name__ == '__main__':
    jupiter_config.set_globals() 
    app_name = jupiter_config.APP_OPTION
    k8s_stream_scheduler(app_name)