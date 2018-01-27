"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

from readconfig import *
import yaml
from kubernetes import client, config
from pprint import *
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
import jupiter_config

def delete_all_profilers():

    """
        This loads the node lists in use
    """
    path1 = 'nodes.txt'
    nodes = read_node_list(path1)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)

    """
        Loop through the list of nodes and deletes the all profiler related k8 deployment, replicaset, pods, and service.
        The deletion should follow this particular order for a proper removal.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g., 
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
    """
    for key in nodes:

        # We have defined the namespace for deployments in jupiter_config
        namespace = jupiter_config.PROFILER_NAMESPACE

        # Get proper handles or pointers to the k8-python tool to call different functions.
        api = client.ExtensionsV1beta1Api()
        body = client.V1DeleteOptions()
        
        # First check if there is a exisitng profiler deployment with
        # the name = key in the respective namespace
        resp = None
        try:
            resp = api.read_namespaced_deployment(key, namespace)
        except ApiException as e:
            print("Exception Occurred")

        # if a deployment with the name = key exists in the namespace, delete it
        if resp:
            del_resp_0 = api.delete_namespaced_deployment(key, namespace, body)
            print("Deployment '%s' Deleted. status='%s'" % (key, str(del_resp_0.status)))


        # Check if there is a replicaset running by using the label "app={key} + profiler" e.g, "app=node1profiler"
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app=" + key + "profiler"
        resp = api.list_replica_set_for_all_namespaces(label_selector = label)
        # if a replicaset exist, delete it
        # pprint(resp)
        # print resp.items[0].metadata.namespace
        for i in resp.items:
            if i.metadata.namespace == namespace:
                del_resp_1 = api.delete_namespaced_replica_set(i.metadata.name, namespace, body)
                print("Relicaset '%s' Deleted. status='%s'" % (key, str(del_resp_1.status)))

        # Check if there is a pod still running by using the label
        resp = None
        api_2 = client.CoreV1Api()
        resp = api_2.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace, body)
            print("Pod Deleted. status='%s'" % str(del_resp_2.status))

        # Check if there is a service running by name = key
        resp = None
        api_2 = client.CoreV1Api()
        try:
            resp = api_2.read_namespaced_service(key, namespace)
        except ApiException as e:
            print("Exception Occurred")
        # if a service is running, kill it
        if resp:
            del_resp_2 = api_2.delete_namespaced_service(key, namespace)
            print("Service Deleted. status='%s'" % str(del_resp_2.status))

        # At this point you should not have any of the profiler related service, pod, or deployment running     