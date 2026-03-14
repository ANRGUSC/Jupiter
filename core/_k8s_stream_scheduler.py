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
from _write_stream_service_specs import write_stream_service_specs
from _write_stream_specs import write_stream_home_specs
import yaml
from kubernetes import client, config
import jupiter_config
import utilities
from kubernetes.client.rest import ApiException
import logging

logging.basicConfig(level = logging.DEBUG)
log = logging.getLogger(__name__)

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
        log.debug(e)
        log.debug("Exception Occurred")

    for key, value in dag.items():
        task = key
        nexthosts = ''

        # Generate the yaml description of the required service for each task
        pod_name = app_name+"-"+task
        try:
            resp = api.read_namespaced_service(pod_name, namespace)
            service_ips[task] = resp.spec.cluster_ip
        except ApiException as e:
            log.debug(e)
            log.debug("Exception Occurred")
    return service_ips




def k8s_stream_scheduler(app_name):
    """
        This script deploys CIRCE in the system. 
    """
    

    jupiter_config.set_globals()

    sys.path.append(jupiter_config.STREAM_PATH)

    # Load kubernetes instance configuration from admin.conf
    # (set KUBECONFIG_PATH in jupiter_config.py)
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)

    # Namespace for deployments is defined in jupiter_config
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE

    # Get handles to the k8s Python client APIs
    api = client.CoreV1Api()
    k8s_apps = client.AppsV1Api()

    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = utilities.k8s_read_dag(path1)
    # get DAG and home machine info
    first_task = dag_info[0]
    dag = dag_info[1]

    log.debug('DAG info:')
    log.debug(dag)

    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes,datasources = utilities.k8s_get_all_elements(path2)

    service_ips = {}; #list of all service IPs
    
    for i in datasources:
        log.debug('Data source information')
        log.debug('First create the home node service')
        home_name =app_name+"-stream"+i
        home_body = write_stream_service_specs(name = home_name)
        
        try:
            ser_resp = api.create_namespaced_service(namespace, home_body)
            log.debug("Home service created. status = '%s'" % str(ser_resp.status))
            resp = api.read_namespaced_service(home_name, namespace)
            service_ips['home'] = resp.spec.cluster_ip
        except ApiException as e:
            log.debug(e)
            log.debug("Exception Occurred")

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
            resp = k8s_apps.create_namespaced_deployment(body = home_dep, namespace = namespace)
            log.debug("Home deployment created")
            log.debug("Home deployment created. status = '%s'" % str(resp.status))
        except ApiException as e:
            log.debug(e)

   
if __name__ == '__main__':
    jupiter_config.set_globals() 
    app_name = jupiter_config.APP_OPTION
    k8s_stream_scheduler(app_name)