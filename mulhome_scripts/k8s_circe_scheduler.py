__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,  Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

import sys
sys.path.append("../")

import time
import os
from os import path
from multiprocessing import Process
from write_circe_service_specs import *
from write_circe_specs import *
import yaml
from kubernetes import client, config
from pprint import *
import jupiter_config
#from utilities import *
import utilities


def check_status_circe(dag,app_name):
    """
    This function prints out all the tasks that are not running.
    If all the tasks are running: return ``True``; else return ``False``.
    """

    jupiter_config.set_globals()

    sys.path.append(jupiter_config.CIRCE_PATH)
    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE


    # We have defined the namespace for deployments in jupiter_config

    # Get proper handles or pointers to the k8-python tool to call different functions.
    extensions_v1_beta1_api = client.ExtensionsV1beta1Api()
    v1_delete_options = client.V1DeleteOptions()
    core_v1_api = client.CoreV1Api()

    result = True
    for key, value in dag.items():
        # First check if there is a deployment existing with
        # the name = key in the respective namespac    # Check if there is a replicaset running by using the label app={key}
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app=" + app_name+'-'+key

        resp = None

        resp = core_v1_api.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            a=resp.items[0]
            if a.status.phase != "Running":
                print("Pod Not Running", key)
                result = False

            # print("Pod Deleted. status='%s'" % str(del_resp_2.status))

    if result:
        print("All systems GOOOOO!!")
    else:
        print("Wait before trying again!!!!")

    return result


# if __name__ == '__main__':
def k8s_circe_scheduler(dag_info , temp_info,app_name):
    """
        This script deploys CIRCE in the system. 
    """

    jupiter_config.set_globals()
    
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
    
    home_name =app_name+"-home"
    home_body = write_circe_service_specs(name = home_name)
    ser_resp = api.create_namespaced_service(namespace, home_body)
    print("Home service created. status = '%s'" % str(ser_resp.status))

    try:
        resp = api.read_namespaced_service(home_name, namespace)
    except ApiException as e:
        print("Exception Occurred")

    service_ips['home'] = resp.spec.cluster_ip
    print(resp.spec.cluster_ip)

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
        pod_name = app_name+"-"+task
        body = write_circe_service_specs(name = pod_name)

        # Call the Kubernetes API to create the service
        ser_resp = api.create_namespaced_service(namespace, body)
        print("Service created. status = '%s'" % str(ser_resp.status))
    
        try:
            resp = api.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            print("Exception Occurred")

        # print resp.spec.cluster_ip
        service_ips[task] = resp.spec.cluster_ip
    
    all_node_ips = ':'.join(service_ips.values())
    all_node = ':'.join(service_ips.keys())

    print(service_ips)
    print(service_ips.keys())
    print(service_ips.values())
    print(all_node)
    """
    All services have started for CIRCE and deployment is yet to begin
    """

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
        print(key)
        print(value)
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
    
        pod_name = app_name+"-"+task
        #Generate the yaml description of the required deployment for each task
        dep = write_circe_deployment_specs(flag = str(flag), inputnum = str(inputnum), name = pod_name, node_name = hosts.get(task)[1],
            image = jupiter_config.WORKER_IMAGE, child = nexthosts, task_name=task,
            child_ips = next_svc, host = hosts.get(task)[1], dir = '{}',
            home_node_ip = service_ips.get('home'),
            own_ip = service_ips[task],
            all_node = all_node,
            all_node_ips = all_node_ips)
        pprint(dep)
        

        # # Call the Kubernetes API to create the deployment
        resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
        print("Deployment created. status = '%s'" % str(resp.status))

    while 1:
        if check_status_circe(dag,app_name):
            break
        time.sleep(30)

    home_name =app_name+"-home"
    home_dep = write_circe_home_specs(name=home_name,image = jupiter_config.HOME_IMAGE, 
                                host = jupiter_config.HOME_NODE, 
                                child = jupiter_config.HOME_CHILD,
                                child_ips = service_ips.get(jupiter_config.HOME_CHILD), 
                                dir = '{}')
    print(home_dep)
    resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
    print("Home deployment created. status = '%s'" % str(resp.status))

    pprint(service_ips)
    
