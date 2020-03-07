__author__ = "Quynh Nguyen, Pradipta Ghosh and  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "4.0"

import sys
sys.path.append("../")
import utilities
import yaml
from kubernetes import client, config
from pprint import *
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
import jupiter_config
import time

def delete_all_stream(app_name):
    """Tear down all CIRCE deployments.
    """
    
    jupiter_config.set_globals()
    
    """
        This loads the task graph
    """
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = utilities.k8s_read_config(path1)
    dag = dag_info[1]
    path2 = jupiter_config.HERE + 'nodes.txt'
    node_list, homes,datasources = utilities.k8s_get_all_elements(path2)

    print('Starting to teardown the datasources')


    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)


    # We have defined the namespace for deployments in jupiter_config
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE

    # Get proper handles or pointers to the k8-python tool to call different functions.
    extensions_v1_beta1_api = client.ExtensionsV1beta1Api()
    v1_delete_options = client.V1DeleteOptions()
    core_v1_api = client.CoreV1Api()

    for datasource in datasources:
        print('Data source information')
 
        #delete home deployment and service
        home_name =app_name+"-stream"+datasource
        print(home_name)
        #home_name ="home"
        resp = None
        try:
            resp = extensions_v1_beta1_api.read_namespaced_deployment(home_name, namespace)
        except ApiException as e:
            print("No Such Deplyment Exists")

        # if home exists, delete it 
        if resp:
            del_resp_0 = extensions_v1_beta1_api.delete_namespaced_deployment(home_name, namespace, v1_delete_options)
            print("Deployment '%s' Deleted. status='%s'" % (home_name, str(del_resp_0.status)))

        # Check if there is a replicaset running by using the label app=home
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app="+app_name+"-stream"+datasource
        # label = "app=home"
        resp = extensions_v1_beta1_api.list_namespaced_replica_set(label_selector = label,namespace = namespace)
        # if a replicaset exist, delete it
        
        # print resp.items[0].metadata.namespace
        for i in resp.items:
            if i.metadata.namespace == namespace:
                del_resp_1 = extensions_v1_beta1_api.delete_namespaced_replica_set(i.metadata.name, namespace, v1_delete_options)
                print("Relicaset '%s' Deleted. status='%s'" % (home_name, str(del_resp_1.status)))

        # Check if there is a pod still running by using the label app='home'
        resp = None
        resp = core_v1_api.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace, v1_delete_options)
            print("Home pod Deleted. status='%s'" % str(del_resp_2.status))

        # Check if there is a service running by name = task#
        resp = None
        try:
            resp = core_v1_api.read_namespaced_service(home_name, namespace=namespace)
        except ApiException as e:
            print("Exception Occurred")
        # if a service is running, kill it
        if resp:
            del_resp_2 = core_v1_api.delete_namespaced_service(home_name, namespace, v1_delete_options)
            #del_resp_2 = core_v1_api.delete_namespaced_service(home_name, namespace=namespace)
            print("Service Deleted. status='%s'" % str(del_resp_2.status))   

if __name__ == '__main__':
    jupiter_config.set_globals() 
    app_name = jupiter_config.APP_OPTION
    app_name = app_name+'1'
    delete_all_stream(app_name)