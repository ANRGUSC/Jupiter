__author__ = "Quynh Nguyen, Pradipta Ghosh,  Pranav Sakulkar,  Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

import sys
sys.path.append("../")

import time
import os
from os import path
from multiprocessing import Process
from write_heft_service_specs import *
from write_heft_specs import *
from kubernetes import client, config
from pprint import *
import os
import jupiter_config
from static_assignment import *
import utilities


def write_file(filename,message):
    with open(filename,'a') as f:
        f.write(message)

def k8s_heft_scheduler(profiler_ips, ex_profiler_ips, node_names,app_name):
    """
        This script deploys HEFT in the system. 
    """
    

    jupiter_config.set_globals()

    """
        This loads the node list
    """
    nexthost_ips = ''
    nexthost_names = ''
    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes = utilities.k8s_get_nodes_worker(path2)
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = utilities.k8s_read_dag(path1)
    dag = dag_info[1]

    print('Starting to deploy HEFT')
    if jupiter_config.BOKEH == 3:
        latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(nodes)+len(homes),len(dag))
        start_time = time.time()
        msg = 'HEFT deploystart %f \n'%(start_time)
        write_file(latency_file,msg)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)

    """
        We have defined the namespace for deployments in jupiter_config
    """
    namespace = jupiter_config.MAPPER_NAMESPACE

    """
        Get proper handles or pointers to the k8-python tool to call different functions.
    """
    api = client.CoreV1Api()
    k8s_beta = client.ExtensionsV1beta1Api()

    service_ips = {};

    """
        Loop through the list of nodes and run all WAVE related k8 deployment, replicaset, pods, and service.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g.,
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
    """
    home_name = app_name+'-home'

    home_body = write_heft_service_specs(name = home_name, label = home_name)
    ser_resp = api.create_namespaced_service(namespace, home_body)
    print("Home service created. status = '%s'" % str(ser_resp.status))

    try:
        resp = api.read_namespaced_service(home_name, namespace)
    except ApiException as e:
        print("Exception Occurred")


    service_ips[home_name] = resp.spec.cluster_ip
    home_ip = service_ips[home_name]
    node_profiler_ips = profiler_ips.copy()
    home_profiler_ips = {}
    for key in homes:
        print(key)
        home_profiler_ips[key] = profiler_ips[key]
        del node_profiler_ips[key]

    profiler_ips_str = ' '.join('{0}:{1}'.format(key, val) for key, val in sorted(node_profiler_ips.items()))
    home_profiler_str = ' '.join('{0}:{1}'.format(key, val) for key, val in sorted(home_profiler_ips.items()))
    
    home_dep = write_heft_specs(name = home_name, label = home_name,
                                image = jupiter_config.HEFT_IMAGE,
                                host = jupiter_config.HOME_NODE,
                                node_names = node_names, 
                                home_ip = home_ip,
                                profiler_ips = profiler_ips_str,
                                execution_home_ip = ex_profiler_ips['home'],
                                home_profiler_ip = home_profiler_str,
                                app_name = app_name,
                                app_option = jupiter_config.APP_OPTION)
    resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
    print("Home deployment created. status = '%s'" % str(resp.status))

    pprint(service_ips)
    print('Successfully deploy HEFT')
    if jupiter_config.BOKEH == 3:
        end_time = time.time()
        msg = 'HEFT deployend %f \n'%(end_time)
        write_file(latency_file,msg)
        deploy_time = end_time - start_time
        print('Time to deploy HEFT '+ str(deploy_time))
if __name__ == '__main__':
    k8s_heft_scheduler(profiler_ips,execution_ips)
