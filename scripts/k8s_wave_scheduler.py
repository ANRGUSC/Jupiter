__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")

import time
import os
from os import path
from multiprocessing import Process
from write_wave_service_specs import *
from write_wave_specs import *
from kubernetes import client, config
from pprint import *
import os
import jupiter_config
#from utilities import *
import utilities

def check_status_waves():
    """Verify if all the WAVE home and workers have been deployed and UP in the system.
    """
    jupiter_config.set_globals()


    """
        This loads the node lists in use
    """
    path1 = jupiter_config.HERE + 'nodes.txt'
    nodes = utilities.k8s_get_nodes(path1)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    namespace = jupiter_config.MAPPER_NAMESPACE


    # We have defined the namespace for deployments in jupiter_config

    # Get proper handles or pointers to the k8-python tool to call different functions.
    extensions_v1_beta1_api = client.ExtensionsV1beta1Api()
    v1_delete_options = client.V1DeleteOptions()
    core_v1_api = client.CoreV1Api()

    result = True
    for key in nodes:

        label = "app=wave_" + key
        resp = None

        resp = core_v1_api.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            a=resp.items[0]
            if a.status.phase != "Running":
                print("Pod Not Running", key)
                result = False

    if result:
        print("All systems GOOOOO!!")
    else:
        print("Wait before trying again!!!!")

    return result



# if __name__ == '__main__':
def k8s_wave_scheduler(profiler_ips):
    """
        Deploy WAVE in the system. 
    """
    jupiter_config.set_globals()

    """
        This loads the node list
    """
    all_profiler_ips = ''
    nexthost_ips = ''
    nexthost_names = ''
    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes = utilities.k8s_get_nodes(path2)
    pprint(nodes)

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
    home_body = write_wave_service_specs(name = 'home', label = "wave_home")
    ser_resp = api.create_namespaced_service(namespace, home_body)
    print("Home service created. status = '%s'" % str(ser_resp.status))

    try:
        resp = api.read_namespaced_service('home', namespace)
    except ApiException as e:
        print("Exception Occurred")
    
    service_ips['home'] = resp.spec.cluster_ip
    home_ip = service_ips['home']
    home_name = 'home'

    print(service_ips)

    for i in nodes:

        """
            Generate the yaml description of the required service for each task
        """
        if i != 'home':
            body = write_wave_service_specs(name = i, label = "wave_" + i)

            # Call the Kubernetes API to create the service
    
            try:
                ser_resp = api.create_namespaced_service(namespace, body)
                print("Service created. status = '%s'" % str(ser_resp.status))
                print(i)
                resp = api.read_namespaced_service(i, namespace)
            except ApiException as e:
                print("Exception Occurred")

            # print resp.spec.cluster_ip
            service_ips[i] = resp.spec.cluster_ip
            nexthost_ips = nexthost_ips + ':' + service_ips[i]
            nexthost_names = nexthost_names + ':' + i
            all_profiler_ips = all_profiler_ips + ':' + profiler_ips[i]
    print(service_ips)
    print(nexthost_ips)
    print(nexthost_names)

    print("####################################")
    print(profiler_ips)
    print("####################################")
    print(all_profiler_ips)

    for i in nodes:

        # print nodes[i][0]
        
        """
            We check whether the node is a home / master.
            We do not run the controller on the master.
        """
        if i != 'home':

            """
                Generate the yaml description of the required deployment for WAVE workers
            """
            dep = write_wave_specs(name = i, label = "wave_" + i, image = jupiter_config.WAVE_WORKER_IMAGE,
                                             host = nodes[i][0], all_node = nexthost_names,
                                             all_node_ips = nexthost_ips,
                                             home_ip = home_ip,
                                             home_name = home_name,
                                             serv_ip = service_ips[i],
                                             profiler_ip = profiler_ips[i],
                                             all_profiler_ips = all_profiler_ips)
            # # pprint(dep)
            # # Call the Kubernetes API to create the deployment
            resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
            print("Deployment created. status ='%s'" % str(resp.status))
            


    # have to somehow make sure that the worker nodes are on and working by this time
    
    while 1:
        if check_status_waves():
            break
        time.sleep(30)

    home_dep = write_wave_specs(name = 'home', label = "wave_home",
                                image = jupiter_config.WAVE_HOME_IMAGE, 
                                host = jupiter_config.HOME_NODE, all_node = nexthost_names,
                                             all_node_ips = nexthost_ips,
                                             home_ip = home_ip,
                                             home_name = home_name,
                                             serv_ip = service_ips['home'],
                                             profiler_ip = profiler_ips['home'],
                                             all_profiler_ips = all_profiler_ips)
    resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
    print("Home deployment created. status = '%s'" % str(resp.status))

    pprint(service_ips)