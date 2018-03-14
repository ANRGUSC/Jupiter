"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import sys
sys.path.append("../")
import jupiter_config

import time
import os
from os import path
from multiprocessing import Process
from write_deployment_specs import *
from write_service_specs import *
from write_home_specs import *
import yaml
from kubernetes import client, config
from pprint import *

# if __name__ == '__main__':
def k8s_circe_scheduler(dag_info , temp_info):
    sys.path.append(jupiter_config.CIRCE_PATH)
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

    #get DAG and home machine info
    first_task = dag_info[0]
    dag = dag_info[1]
    hosts = temp_info[2]
    print("hosts:")
    pprint(hosts)
    print(len(dag_info))
    pprint(dag_info[0])
    pprint(dag_info[1])
    pprint(dag_info[2])
    service_ips = {}; #list of all service IPs

    """
        First create the home node's service.
    """
    
    home_body = write_service_specs(name = 'home')
    ser_resp = api.create_namespaced_service(namespace, home_body)
    print("Home service created. status = '%s'" % str(ser_resp.status))

    try:
        resp = api.read_namespaced_service('home', namespace)
    except ApiException as e:
        print("Exception Occurred")

    service_ips['home'] = resp.spec.cluster_ip

    """
        Iterate through the list of tasks and run the related k8 deployment, replicaset, pod, and service on the respective node.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g., 
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
    """ 
   
    for key, value in dag.items():

        task = key
        nexthosts = ''
 
        """
            Generate the yaml description of the required service for each task
        """
        body = write_service_specs(name = task)

        # Call the Kubernetes API to create the service
        ser_resp = api.create_namespaced_service(namespace, body)
        print("Service created. status = '%s'" % str(ser_resp.status))
    
        try:
            resp = api.read_namespaced_service(task, namespace)
        except ApiException as e:
            print("Exception Occurred")

        # print resp.spec.cluster_ip
        service_ips[task] = resp.spec.cluster_ip
    
    all_node_ips = ':'.join(service_ips.values())
    all_node = ':'.join(service_ips.keys())
    print(all_node)
    """
    All services have started for CIRCE and deployment is yet to begin
    In the meantime, start dft_coded_detector services and their deployments
    """


    # branch_number = 3 # how many aggregation points do you have?
    # dft_coded_service_ips = []
    # for idx in range(branch_number):
    #     path = "nodes_dft_coded" + str(idx)+ ".txt"
    #     dft_coded_service_ips.append(launch_dft_coding_services(path=path))
    #     launch_dft_coding_deployments(dft_coded_service_ips[idx], path=path, masterIP=service_ips['dftdetector'+str(idx)])
    #     all_node_ips = all_node_ips + ":" + dft_coded_service_ips[idx]
    #     all_node = all_node + (":dftslave%d0:dftslave%d1:dftslave%d2"%(idx,idx,idx))
    
    """
    Let's start the TeraSort coded detectors now!!!
    """
    # tera_master_ips = []
    # for idx in range(branch_number):
    #     path = "nodes_tera_coded" + str(idx)+ ".txt"
    #     tera_coded_service_ips, master_ip = launch_tera_coding_services(path=path)
    #     launch_tera_coding_deployments(tera_coded_service_ips, path=path)
    #     tera_master_ips.append(master_ip)

    """
    Start circe
    """
    for key, value in dag.items():

        task = key
        nexthosts = ''
        next_svc = ''

        """
            We inject the host info for the child task via an environment variable valled CHILD_NODES to each pod/deployment.
            We perform it by concatenating the child-hosts via delimeter ':'
            For example if the child nodes are k8node1 and k8node2, we will set CHILD_NODES=k8node1:k8node2
            Note that the k8node1 and k8node2 in the example are the unique node ids of the kubernets cluster nodes.
        """
        inputnum = str(value[0])
        flag = str(value[1])

        for i in range(2,len(value)):
            if i != 2:
                nexthosts = nexthosts + ':'
            nexthosts = nexthosts + str(hosts.get(value[i])[0])

        for i in range(2, len(value)): 
            if i != 2:
                next_svc = next_svc + ':'
            next_svc = next_svc + str(service_ips.get(value[i]))
        print("NEXT HOSTS")
        print(nexthosts)
        print("NEXT SVC")
        print(next_svc)
    
        
        #Generate the yaml description of the required deployment for each task
        dep = write_deployment_specs(flag = str(flag), inputnum = str(inputnum), name = task, node_name = hosts.get(task)[1],
            image = jupiter_config.WORKER_IMAGE, child = nexthosts, 
            child_ips = next_svc, host = hosts.get(task)[1], dir = '{}',
            home_node_ip = service_ips.get("home"),
            own_ip = service_ips[key],
            all_node = all_node,
            all_node_ips = all_node_ips,)
        pprint(dep)
        

        # # Call the Kubernetes API to create the deployment
        resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
        print("Deployment created. status = '%s'" % str(resp.status))


    home_dep = write_home_specs(image = jupiter_config.HOME_IMAGE, 
                                host = jupiter_config.HOME_NODE, 
                                child_ips = service_ips.get(jupiter_config.HOME_CHILD), dir = '{}')
    resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
    print("Home deployment created. status = '%s'" % str(resp.status))

    pprint(service_ips)
    

