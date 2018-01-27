"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import time
import os
from os import path
from multiprocessing import Process
from write_profiler_service_specs import *
from readconfig import *
from write_profiler_specs import *
from kubernetes import client, config
from pprint import *
import os
import jupiter_config



# if __name__ == '__main__':
def k8s_profiler_scheduler(): 
    """
        This loads the task graph and node list
    """
    nexthost_ips = ''
    nexthost_names = ''
    path2 = 'nodes.txt'
    nodes = read_node_list(path2)


    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """    
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    
    """
        We have defined the namespace for deployments in jupiter_config
    """
    namespace = jupiter_config.PROFILER_NAMESPACE
    
    """
        Get proper handles or pointers to the k8-python tool to call different functions.
    """
    api = client.CoreV1Api()
    k8s_beta = client.ExtensionsV1beta1Api()

    # first_task = dag_info[0]
    # dag = dag_info[1]
    # hosts = temp_info[2]
    # print("hosts:")
    # pprint(hosts)
    # print(len(dag_info))
    # pprint(dag_info[0])
    # pprint(dag_info[1])
    # pprint(dag_info[2])
    service_ips = {}; 
    pprint(nodes)

    # # get the list of nodes
    # ret = v1.list_node()

    """
        Loop through the list of nodes and run all profiler related k8 deployment, replicaset, pods, and service.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g., 
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
    """   
    home_body = write_profiler_service_specs(name = 'home', label = "homeprofiler")
    ser_resp = api.create_namespaced_service(namespace, home_body)
    print("Home service created. status = '%s'" % str(ser_resp.status))

    try:
        resp = api.read_namespaced_service('home', namespace)
    except ApiException as e:
        print("Exception Occurred")
    
    service_ips['home'] = resp.spec.cluster_ip
    # nexthost_ips = service_ips['home']
    # nexthost_names = 'home'

    print(service_ips)

    for i in nodes:

        """
            Generate the yaml description of the required service for each task
        """
        if i != 'home':
            body = write_profiler_service_specs(name = i, label = i + "profiler")

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
    print(service_ips)
    print(nexthost_ips)
    print(nexthost_names)

    for i in nodes:

        # print nodes[i][0]
        
        """
            We check whether the node is a scheduler.
            Since we do not run any task on the scheduler, we donot run any profiler on it as well.
        """
        if i != 'home':

            """
                Generate the yaml description of the required deployment for the profiles
            """
            dep = write_profiler_specs(name = i, label = i + "profiler", image = jupiter_config.PROFILER_WORKER_IMAGE,
                                             host = nodes[i][0], dir = '{}', all_node = nexthost_names,
                                             all_node_ips = nexthost_ips,
                                             serv_ip = service_ips[i])
            # # pprint(dep)
            # # Call the Kubernetes API to create the deployment
            resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
            print("Deployment created. status ='%s'" % str(resp.status))
            


    # have to somehow make sure that the worker nodes are on and working by this time
    time.sleep(30)
    home_dep = write_profiler_specs(name = 'home', label = "homeprofiler",
                                image = jupiter_config.PROFILER_HOME_IMAGE, 
                                host = jupiter_config.HOME_NODE, 
                                dir = '{}', all_node = nexthost_names,
                                             all_node_ips = nexthost_ips,
                                             serv_ip = service_ips['home'])
    resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
    print("Home deployment created. status = '%s'" % str(resp.status))

    pprint(service_ips)
    return(service_ips)

