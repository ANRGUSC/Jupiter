__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
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
import utilities
import logging

logging.basicConfig(level = logging.DEBUG)

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
            logging.debug("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # logging.debug(resp.spec.cluster_ip)
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
            logging.debug("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # logging.debug(resp.spec.cluster_ip)
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
        logging.debug("Exception Occurred")
    # if a service is running, kill it
    if resp:
        logging.debug(resp.spec.cluster_ip)
        mapping[key] = resp.spec.cluster_ip

    # At this point you should not have any of the profiler related service, pod, or deployment running
    return mapping

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
        logging.debug(e)
        logging.debug("Exception Occurred")

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
            logging.debug(e)
            logging.debug("Exception Occurred")
    return service_ips


def get_service_global(app_name):
    jupiter_config.set_globals()
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE
    api = client.CoreV1Api()

    service_ip_global = None
    home_name =app_name+"-globalinfohome"
    try:
        resp = api.read_namespaced_service(home_name, namespace)
        service_ip_global = resp.spec.cluster_ip
    except ApiException as e:
        logging.debug(e)
        logging.debug("Exception Occurred")

    return service_ip_global

def get_service_sinks(app_name):
    jupiter_config.set_globals()
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE
    api = client.CoreV1Api()

    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes,datasources,datasinks = utilities.k8s_get_all_elements(path2)

    service_ips = {}; #list of all service IPs
    for i in datasinks:
        sink_name =app_name+"-sink"+i
        try:
            resp = api.read_namespaced_service(sink_name, namespace)
            service_ips[sink_name] = resp.spec.cluster_ip
        except ApiException as e:
            logging.debug(e)
            logging.debug("Exception Occurred")

    return service_ips





if __name__ == '__main__':
    logging.debug(get_all_profilers())