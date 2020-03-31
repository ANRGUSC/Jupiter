__author__ = "Quynh Nguyen, Pradipta Ghosh, Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

import sys
sys.path.append("../")

from utilities import *
import yaml
from kubernetes import client, config
from pprint import *
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
import jupiter_config
import logging
from delete_all_heft import *
from delete_all_waves import *


logging.basicConfig(level = logging.DEBUG)

def write_file(filename,message):
    with open(filename,'a') as f:
        f.write(message)

def delete_all_pricing_circe(app_name):
    """Tear down all CIRCE deployments.
    """
    jupiter_config.set_globals()
    
    """
        This loads the task graph
    """
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = k8s_read_config(path1)
    dag = dag_info[1]

    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes = k8s_get_nodes(path2)

    logging.debug('Starting to teardown pricing CIRCE')
    if jupiter_config.BOKEH == 3:
        latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(nodes),len(dag))
        start_time = time.time()
        if jupiter_config.PRICING == 1:
            msg = 'PRICEpush teardownstart %f \n'%(start_time)
        elif jupiter_config.PRICING == 2:
            msg = 'PRICEevent teardownstart %f \n'%(start_time)
        elif jupiter_config.PRICING == 4:
            msg = 'PRICEdecoupled teardownstart %f \n'%(start_time)
        write_file(latency_file,msg)


    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)


    # We have defined the namespace for deployments in jupiter_config
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE

    # Get proper handles or pointers to the k8-python tool to call different functions.
    k8s_apps_v1 = client.AppsV1Api()
    v1_delete_options = client.V1DeleteOptions()
    core_v1_api = client.CoreV1Api()

    """
        Loop through the list of tasks in the dag and delete the respective k8 deployment, replicaset, pods, and service.
        The deletion should follow this particular order for a proper removal.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g., 
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
    """
    for key, value in dag.items():

        pod_name = app_name+"-"+key

        # First check if there is a deployment existing with
        # the name = key in the respective namespace
        resp = None
        try:
            resp = k8s_apps_v1.read_namespaced_deployment(pod_name, namespace)
        except ApiException as e:
            logging.debug("No Such Deplyment Exists")

        # if a deployment with the name = key exists in the namespace, delete it
        if resp:
            # del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace, v1_delete_options)
            del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace)

            logging.debug("Deployment '%s' Deleted. status='%s'" % (key, str(del_resp_0.status)))


        # Check if there is a replicaset running by using the label app={key}
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app="+app_name+'-' + key
        resp = k8s_apps_v1.list_namespaced_replica_set(label_selector = label,namespace=namespace)
        # if a replicaset exist, delete it
        
        # logging.debug resp.items[0].metadata.namespace
        for i in resp.items:
            if i.metadata.namespace == namespace:
                try:
                    del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace)
                    # del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace,v1_delete_options)
                    logging.debug("Relicaset '%s' Deleted. status='%s'" % (key, str(del_resp_1.status)))
                except ApiException as e:
                    logging.debug("Exception when calling AppsV1Api->delete_namespaced_replica_set: %s",e)
        # Check if there is a pod still running by using the label app={key}
        resp = None

        resp = core_v1_api.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            # del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace, v1_delete_options)
            del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace)

            logging.debug("Pod Deleted. status='%s'" % str(del_resp_2.status))

        # Check if there is a service running by name = task#
        resp = None
        try:
            resp = core_v1_api.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # del_resp_2 = core_v1_api.delete_namespaced_service(pod_name, namespace, v1_delete_options)
            del_resp_2 = core_v1_api.delete_namespaced_service(pod_name, namespace)
            logging.debug("Service Deleted. status='%s'" % str(del_resp_2.status))

        # At this point you should not have any of the related service, pods, deployment running
    #end for

    home_name =app_name+"-home"
    #delete home deployment and service
    resp = None
    try:
        resp = k8s_apps_v1.read_namespaced_deployment(home_name, namespace)
    except ApiException as e:
        logging.debug("No Such Deplyment Exists")

    # if home exists, delete it 
    if resp:
        del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(home_name, namespace=namespace, body=v1_delete_options)
        logging.debug("Deployment '%s' Deleted. status='%s'" % (home_name, str(del_resp_0.status)))

    # Check if there is a replicaset running by using the label app=home
    # The label of kubernets are used to identify replicaset associate to each task
    label = "app="+app_name+"-home"
    resp = k8s_apps_v1.list_namespaced_replica_set(label_selector = label,namespace=namespace)
    # if a replicaset exist, delete it
    
    # logging.debug resp.items[0].metadata.namespace
    for i in resp.items:
        if i.metadata.namespace == namespace:
            try:
                # del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace, v1_delete_options)
                del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace)
                logging.debug("Relicaset '%s' Deleted. status='%s'" % ('home', str(del_resp_1.status)))
            except ApiException as e:
                logging.debug("Exception when calling AppsV1Api->delete_namespaced_replica_set: %s",e)

    # Check if there is a pod still running by using the label app='home'
    resp = None
    resp = core_v1_api.list_namespaced_pod(namespace=namespace, label_selector = label)
    # if a pod is running just delete it
    if resp.items:
        # del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace, v1_delete_options)
        del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace)
        logging.debug("Home pod Deleted. status='%s'" % str(del_resp_2.status))

    # Check if there is a service running by name = task#
    resp = None
    try:
        resp = core_v1_api.read_namespaced_service(home_name, namespace=namespace)
    except ApiException as e:
        logging.debug("Exception Occurred")
    # if a service is running, kill it
    if resp:
        # del_resp_2 = core_v1_api.delete_namespaced_service(home_name, namespace, v1_delete_options)
        del_resp_2 = core_v1_api.delete_namespaced_service(home_name, namespace=namespace)
        logging.debug("Service Deleted. status='%s'" % str(del_resp_2.status))    

    for key in nodes:

        
        pod_name = app_name +'-'+key

        # Get proper handles or pointers to the k8-python tool to call different functions.
        k8s_apps_v1 = client.AppsV1Api()
        body = client.V1DeleteOptions()
        
        # First check if there is a exisitng profiler deployment with
        # the name = key in the respective namespace
        logging.debug(pod_name)
        resp = None
        try:
            resp = k8s_apps_v1.read_namespaced_deployment(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")

        # if a deployment with the name = key exists in the namespace, delete it
        if resp:
            # del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace, body)
            del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace)

            logging.debug("Deployment '%s' Deleted. status='%s'" % (key, str(del_resp_0.status)))


        # Check if there is a replicaset running by using the label "app=wave_" + key e.g, "app=wave_node1"
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app=" + app_name+'-'+ key
        resp = k8s_apps_v1.list_namespaced_replica_set(label_selector = label,namespace=namespace)
        # if a replicaset exist, delete it
        # pprint(resp)
        # logging.debug resp.items[0].metadata.namespace
        for i in resp.items:
            if i.metadata.namespace == namespace:
                try:
                    # del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace, body)
                    del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace)

                    logging.debug("Relicaset '%s' Deleted. status='%s'" % (key, str(del_resp_1.status)))
                except ApiException as e:
                    logging.debug("Exception when calling AppsV1Api->delete_namespaced_replica_set: %s",e)

        # Check if there is a pod still running by using the label
        resp = None
        api_2 = client.CoreV1Api()
        resp = api_2.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            # del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace, body)
            del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace)

            logging.debug("Pod Deleted. status='%s'" % str(del_resp_2.status))

        # Check if there is a service running by name = key
        resp = None
        api_2 = client.CoreV1Api()
        try:
            resp = api_2.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # del_resp_2 = api_2.delete_namespaced_service(pod_name, namespace, v1_delete_options)
            del_resp_2 = api_2.delete_namespaced_service(pod_name, namespace)
            logging.debug("Service Deleted. status='%s'" % str(del_resp_2.status))

    if jupiter_config.SCHEDULER == 0 or jupiter_config.SCHEDULER == 3:
        delete_all_heft(app_name)
    else:
        delete_all_waves(app_name)

    logging.debug('Successfully teardown pricing CIRCE ')
    if jupiter_config.BOKEH == 3:
        end_time = time.time()
        if jupiter_config.PRICING == 1:
            msg = 'PRICEpush teardownend %f \n'%(start_time)
        elif jupiter_config.PRICING == 2:
            msg = 'PRICEevent teardownend %f \n'%(start_time)
        elif jupiter_config.PRICING == 4:
            msg = 'PRICEdecoupled teardownend %f \n'%(start_time)
        write_file(latency_file,msg)
        teardown_time = end_time - start_time
        logging.debug('Time to teardown CIRCE'+ str(teardown_time))  


def delete_all_decoupled_pricing_circe(app_name):
    """Tear down all CIRCE deployments.
    """
    jupiter_config.set_globals()
    
    """
        This loads the task graph
    """
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = k8s_read_config(path1)
    dag = dag_info[1]

    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes = k8s_get_nodes(path2)

    logging.debug('Starting to teardown decoupled pricing CIRCE')
    if jupiter_config.BOKEH == 3:
        latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(nodes),len(dag))
        start_time = time.time()
        msg = 'PRICEintegrated teardownstart %f \n'%(start_time)
        write_file(latency_file,msg)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)


    # We have defined the namespace for deployments in jupiter_config
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE

    # Get proper handles or pointers to the k8-python tool to call different functions.
    k8s_apps_v1 = client.AppsV1Api()
    v1_delete_options = client.V1DeleteOptions()
    core_v1_api = client.CoreV1Api()

    """
        Loop through the list of tasks in the dag and delete the respective k8 deployment, replicaset, pods, and service.
        The deletion should follow this particular order for a proper removal.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g., 
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
    """
        # At this point you should not have any of the related service, pods, deployment running
    #end for

    home_name =app_name+"-home"
    #delete home deployment and service
    resp = None
    try:
        resp = k8s_apps_v1.read_namespaced_deployment(home_name, namespace)
    except ApiException as e:
        logging.debug("No Such Deplyment Exists")

    # if home exists, delete it 
    if resp:
        del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(home_name, namespace=namespace, body=v1_delete_options)
        logging.debug("Deployment '%s' Deleted. status='%s'" % (home_name, str(del_resp_0.status)))

    # Check if there is a replicaset running by using the label app=home
    # The label of kubernets are used to identify replicaset associate to each task
    label = "app="+app_name+"-home"
    resp = k8s_apps_v1.list_namespaced_replica_set(label_selector = label,namespace=namespace)
    # if a replicaset exist, delete it
    
    # logging.debug resp.items[0].metadata.namespace
    for i in resp.items:
        if i.metadata.namespace == namespace:
            try:
                # del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace, v1_delete_options)
                del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace)
                logging.debug("Relicaset '%s' Deleted. status='%s'" % ('home', str(del_resp_1.status)))
            except ApiException as e:
                logging.debug("Exception when calling AppsV1Api->delete_namespaced_replica_set: %s",e)

    # Check if there is a pod still running by using the label app='home'
    resp = None
    resp = core_v1_api.list_namespaced_pod(namespace=namespace, label_selector = label)
    # if a pod is running just delete it
    if resp.items:
        # del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace, v1_delete_options)
        del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace)

        logging.debug("Home pod Deleted. status='%s'" % str(del_resp_2.status))

    # Check if there is a service running by name = task#
    resp = None
    try:
        resp = core_v1_api.read_namespaced_service(home_name, namespace=namespace)
    except ApiException as e:
        logging.debug("Exception Occurred")
    # if a service is running, kill it
    if resp:
        # del_resp_2 = core_v1_api.delete_namespaced_service(home_name, namespace, v1_delete_options)
        del_resp_2 = core_v1_api.delete_namespaced_service(home_name, namespace=namespace)
        logging.debug("Service Deleted. status='%s'" % str(del_resp_2.status))    

    for key in nodes:

        
        pod_name = app_name +'-'+key

        # Get proper handles or pointers to the k8-python tool to call different functions.
        k8s_apps_v1 = client.AppsV1Api()
        body = client.V1DeleteOptions()
        
        # First check if there is a exisitng profiler deployment with
        # the name = key in the respective namespace
        logging.debug(pod_name)
        resp = None
        try:
            resp = k8s_apps_v1.read_namespaced_deployment(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")

        # if a deployment with the name = key exists in the namespace, delete it
        if resp:
            # del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace, body)
            del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace)
            logging.debug("Deployment '%s' Deleted. status='%s'" % (key, str(del_resp_0.status)))


        # Check if there is a replicaset running by using the label "app=wave_" + key e.g, "app=wave_node1"
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app=" + app_name+'-'+ key
        resp = k8s_apps_v1.list_namespaced_replica_set(label_selector = label,namespace=namespace)
        # if a replicaset exist, delete it
        # pprint(resp)
        # logging.debug resp.items[0].metadata.namespace
        for i in resp.items:
            if i.metadata.namespace == namespace:
                try:
                    # del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace, body)
                    del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace)
                    logging.debug("Relicaset '%s' Deleted. status='%s'" % (key, str(del_resp_1.status)))
                except ApiException as e:
                    logging.debug("Exception when calling AppsV1Api->delete_namespaced_replica_set: %s",e)
        # Check if there is a pod still running by using the label
        resp = None
        api_2 = client.CoreV1Api()
        resp = api_2.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            # del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace, body)
            del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace)
            logging.debug("Pod Deleted. status='%s'" % str(del_resp_2.status))

        # Check if there is a service running by name = key
        resp = None
        api_2 = client.CoreV1Api()
        try:
            resp = api_2.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # del_resp_2 = api_2.delete_namespaced_service(pod_name, namespace, v1_delete_options)
            del_resp_2 = api_2.delete_namespaced_service(pod_name, namespace)
            logging.debug("Service Deleted. status='%s'" % str(del_resp_2.status))

    for key in nodes:

        
        pod_name = app_name +'-controller'+key

        # Get proper handles or pointers to the k8-python tool to call different functions.
        k8s_apps_v1 = client.AppsV1Api()
        body = client.V1DeleteOptions()
        
        # First check if there is a exisitng profiler deployment with
        # the name = key in the respective namespace
        logging.debug(pod_name)
        resp = None
        try:
            resp = k8s_apps_v1.read_namespaced_deployment(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")

        # if a deployment with the name = key exists in the namespace, delete it
        if resp:
            # del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace, body)
            del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace)
            logging.debug("Deployment '%s' Deleted. status='%s'" % (key, str(del_resp_0.status)))


        # Check if there is a replicaset running by using the label "app=wave_" + key e.g, "app=wave_node1"
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app=" + app_name+'-controller'+key
        resp = k8s_apps_v1.list_namespaced_replica_set(label_selector = label,namespace=namespace)
        # if a replicaset exist, delete it
        # pprint(resp)
        # logging.debug resp.items[0].metadata.namespace
        for i in resp.items:
            if i.metadata.namespace == namespace:
                try:
                    # del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace, body)
                    del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace)

                    logging.debug("Relicaset '%s' Deleted. status='%s'" % (key, str(del_resp_1.status)))
                except ApiException as e:
                    logging.debug("Exception when calling AppsV1Api->delete_namespaced_replica_set: %s",e)
        # Check if there is a pod still running by using the label
        resp = None
        api_2 = client.CoreV1Api()
        resp = api_2.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            # del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace, body)
            del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace)
            logging.debug("Pod Deleted. status='%s'" % str(del_resp_2.status))

        # Check if there is a service running by name = key
        resp = None
        api_2 = client.CoreV1Api()
        try:
            resp = api_2.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # del_resp_2 = api_2.delete_namespaced_service(pod_name, namespace, v1_delete_options)
            del_resp_2 = api_2.delete_namespaced_service(pod_name, namespace)
            logging.debug("Service Deleted. status='%s'" % str(del_resp_2.status))

    logging.debug('Successfully teardown decoupled CIRCE ')
    if jupiter_config.BOKEH == 3:
        end_time = time.time()
        msg = 'PRICEintegrated teardownend %f \n'%(end_time)
        write_file(latency_file,msg)
        teardown_time = end_time - start_time
        logging.debug('Time to teardown PRICEING CIRCE'+ str(teardown_time)) 

def delete_all_integrated_pricing_circe(app_name):
    """Tear down all CIRCE deployments.
    """
    jupiter_config.set_globals()
    
    """
        This loads the task graph
    """
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = k8s_read_config(path1)
    dag = dag_info[1]

    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes = k8s_get_nodes(path2)

    logging.debug('Starting to teardown integrated pricing CIRCE')
    if jupiter_config.BOKEH == 3:
        latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(nodes),len(dag))
        start_time = time.time()
        msg = 'PRICEintegrated teardownstart %f \n'%(start_time)
        write_file(latency_file,msg)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)


    # We have defined the namespace for deployments in jupiter_config
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE

    # Get proper handles or pointers to the k8-python tool to call different functions.
    v1_delete_options = client.V1DeleteOptions()
    k8s_apps_v1 = client.AppsV1Api()
    core_v1_api = client.CoreV1Api()

    """
        Loop through the list of tasks in the dag and delete the respective k8 deployment, replicaset, pods, and service.
        The deletion should follow this particular order for a proper removal.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g., 
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
    """
        # At this point you should not have any of the related service, pods, deployment running
    #end for

    home_name =app_name+"-home"
    #delete home deployment and service
    resp = None
    try:
        resp = k8s_apps_v1.read_namespaced_deployment(home_name, namespace)
    except ApiException as e:
        logging.debug("No Such Deplyment Exists")

    # if home exists, delete it 
    if resp:
        del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(home_name, namespace=namespace, body=v1_delete_options)
        logging.debug("Deployment '%s' Deleted. status='%s'" % (home_name, str(del_resp_0.status)))

    # Check if there is a replicaset running by using the label app=home
    # The label of kubernets are used to identify replicaset associate to each task
    label = "app="+app_name+"-home"
    resp = k8s_apps_v1.list_namespaced_replica_set(label_selector = label,namespace=namespace)
    # if a replicaset exist, delete it
    
    # logging.debug resp.items[0].metadata.namespace
    for i in resp.items:
        if i.metadata.namespace == namespace:
            try:
                # del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace, v1_delete_options)
                del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace)

                logging.debug("Relicaset '%s' Deleted. status='%s'" % ('home', str(del_resp_1.status)))
            except ApiException as e:
                logging.debug("Exception when calling AppsV1Api->delete_namespaced_replica_set: %s",e)

    # Check if there is a pod still running by using the label app='home'
    resp = None
    resp = core_v1_api.list_namespaced_pod(namespace=namespace, label_selector = label)
    # if a pod is running just delete it
    if resp.items:
        # del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace, v1_delete_options)
        del_resp_2 = core_v1_api.delete_namespaced_pod(resp.items[0].metadata.name, namespace)

        logging.debug("Home pod Deleted. status='%s'" % str(del_resp_2.status))

    # Check if there is a service running by name = task#
    resp = None
    try:
        resp = core_v1_api.read_namespaced_service(home_name, namespace=namespace)
    except ApiException as e:
        logging.debug("Exception Occurred")
    # if a service is running, kill it
    if resp:
        # del_resp_2 = core_v1_api.delete_namespaced_service(home_name, namespace, v1_delete_options)
        del_resp_2 = core_v1_api.delete_namespaced_service(home_name, namespace=namespace)
        logging.debug("Service Deleted. status='%s'" % str(del_resp_2.status))    

    for key in nodes:

        
        pod_name = app_name +'-'+key

        # Get proper handles or pointers to the k8-python tool to call different functions.
        k8s_apps_v1 = client.AppsV1Api()
        body = client.V1DeleteOptions()
        
        # First check if there is a exisitng profiler deployment with
        # the name = key in the respective namespace
        logging.debug(pod_name)
        resp = None
        try:
            resp = k8s_apps_v1.read_namespaced_deployment(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")

        # if a deployment with the name = key exists in the namespace, delete it
        if resp:
            # del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace, body)
            del_resp_0 = k8s_apps_v1.delete_namespaced_deployment(pod_name, namespace)

            logging.debug("Deployment '%s' Deleted. status='%s'" % (key, str(del_resp_0.status)))


        # Check if there is a replicaset running by using the label "app=wave_" + key e.g, "app=wave_node1"
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app=" + app_name+'-'+ key
        resp = k8s_apps_v1.list_namespaced_replica_set(label_selector = label,namespace=namespace)
        # if a replicaset exist, delete it
        # pprint(resp)
        # logging.debug resp.items[0].metadata.namespace
        for i in resp.items:
            if i.metadata.namespace == namespace:
                try:
                    # del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace, body)
                    del_resp_1 = k8s_apps_v1.delete_namespaced_replica_set(i.metadata.name, namespace)

                    logging.debug("Relicaset '%s' Deleted. status='%s'" % (key, str(del_resp_1.status)))
                except ApiException as e:
                    logging.debug("Exception when calling AppsV1Api->delete_namespaced_replica_set: %s",e)

        # Check if there is a pod still running by using the label
        resp = None
        api_2 = client.CoreV1Api()
        resp = api_2.list_namespaced_pod(namespace, label_selector = label)
        # if a pod is running just delete it
        if resp.items:
            # del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace, body)
            del_resp_2 = api_2.delete_namespaced_pod(resp.items[0].metadata.name, namespace)

            logging.debug("Pod Deleted. status='%s'" % str(del_resp_2.status))

        # Check if there is a service running by name = key
        resp = None
        api_2 = client.CoreV1Api()
        try:
            resp = api_2.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            logging.debug("Exception Occurred")
        # if a service is running, kill it
        if resp:
            # del_resp_2 = api_2.delete_namespaced_service(pod_name, namespace, v1_delete_options)
            del_resp_2 = api_2.delete_namespaced_service(pod_name, namespace)
            logging.debug("Service Deleted. status='%s'" % str(del_resp_2.status))

    logging.debug('Successfully teardown integrated CIRCE ')
    if jupiter_config.BOKEH == 3:
        end_time = time.time()
        msg = 'PRICEintegrated teardownend %f \n'%(end_time)
        write_file(latency_file,msg)
        teardown_time = end_time - start_time
        logging.debug('Time to teardown PRICEING CIRCE'+ str(teardown_time))

if __name__ == '__main__':
    jupiter_config.set_globals() 
    app_name = jupiter_config.APP_OPTION
    app_name = app_name+'1'
    pricing_option = jupiter_config.PRICING
    if pricing_option == 1 or pricing_option == 2:
        delete_all_pricing_circe(app_name)
    elif pricing_option==3:
        delete_all_integrated_pricing_circe(app_name)
    else:
        delete_all_decoupled_pricing_circe(app_name)