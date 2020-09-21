__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")

import yaml
from kubernetes import client, config
from pprint import *
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
import jupiter_config
#from utilities import *
import utilities

def get_all_profilers():
    """
        This function loads all of the service ips of network profilers deployments.
    """
    
    jupiter_config.set_globals()

    """
        This loads the node lists in use
    """
    mapping = {}
    path1 = jupiter_config.HERE + 'nodes.txt'
    nodes = utilities.k8s_get_nodes(path1)

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
        label = "app=" + key + "profiler"
        
        resp = None
        api_2 = client.CoreV1Api()
        try:
            resp = api_2.read_namespaced_service(key, namespace)
        except ApiException as e:
            print("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # print(resp.spec.cluster_ip)
            mapping[key] = resp.spec.cluster_ip

    return mapping

        # At this point you should not have any of the profiler related service, pod, or deployment running


def get_all_waves(app_name):
    """
        This function loads all of the service ips of WAVE deployments.
    """
    
    jupiter_config.set_globals()

    mapping = {}

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
        namespace = jupiter_config.MAPPER_NAMESPACE

        # Get proper handles or pointers to the k8-python tool to call different functions.
        api = client.ExtensionsV1beta1Api()
        body = client.V1DeleteOptions()
        
        # First check if there is a exisitng profiler deployment with
        # the name = key in the respective namespace
        #label = "app=wave_" + key
        pod_name = app_name+'-'+key
        
        resp = None
        api_2 = client.CoreV1Api()
        try:
            resp = api_2.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            print("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # print(resp.spec.cluster_ip)
            mapping[key] = resp.spec.cluster_ip
    return mapping
        # At this point you should not have any of the profiler related service, pod, or deployment running

def get_all_execs(app_name):
    """
        This load all of the service ips of execution profiler deployments.
    """
    jupiter_config.set_globals()

    mapping = {}

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

        # We have defined the namespace for deployments in jupiter_config
    namespace = jupiter_config.EXEC_NAMESPACE

    # Get proper handles or pointers to the k8-python tool to call different functions.
    api = client.ExtensionsV1beta1Api()
    body = client.V1DeleteOptions()

    # First check if there is a exisitng profiler deployment with
    # the name = key in the respective namespace
    key = 'home'
    pod_name = app_name+ "-home"

    resp = None
    api_2 = client.CoreV1Api()
    
    try:
        resp = api_2.read_namespaced_service(pod_name, namespace)
    except ApiException as e:
        print("Exception Occurred")
    # if a service is running, kill it
    if resp:
        print(resp.spec.cluster_ip)
        mapping[key] = resp.spec.cluster_ip

    # At this point you should not have any of the profiler related service, pod, or deployment running
    return mapping




if __name__ == '__main__':
    print(get_all_profilers())