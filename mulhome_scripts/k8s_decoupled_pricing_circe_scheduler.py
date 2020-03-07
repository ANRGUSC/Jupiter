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
from write_decoupled_pricing_circe_service_specs import *
from write_decoupled_pricing_circe_specs import *
from kubernetes import client, config
from pprint import *
import os
import jupiter_config
import utilities
import sys, json

def check_status_circe_controllers(app_name):
    """Verify if all the WAVE home and workers have been deployed and UP in the system.
    """
    jupiter_config.set_globals()


    """
        This loads the node lists in use
    """
    path1 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes = utilities.k8s_get_nodes_worker(path1)
    pprint(nodes)

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
    for key in nodes:

        label = "app=%s_wave_"%(app_name)
        label = label + key
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

def check_status_circe_compute(app_name):
    """
    This function prints out all the tasks that are not running.
    If all the tasks are running: return ``True``; else return ``False``.
    """

    jupiter_config.set_globals()

    path1 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes = utilities.k8s_get_nodes_worker(path1)

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
    for key in nodes:
        # First check if there is a deployment existing with
        # the name = key in the respective namespac    # Check if there is a replicaset running by using the label app={key}
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app=" + app_name+'-'+ key 

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
        print("All the computing nodes GOOOOO!!")
    else:
        print("Wait before trying again!!!!")

    return result


def write_file(filename,message):
    with open(filename,'a') as f:
        f.write(message)

# if __name__ == '__main__':
def k8s_decoupled_pricing_controller_scheduler(profiler_ips,app_name,compute_service_ips):
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
    nodes, homes = utilities.k8s_get_nodes_worker(path2)
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
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE
    
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
    home_name = app_name+'-controllerhome'
    home_label = app_name+'-controllerhome'
    home_body = write_decoupled_pricing_circe_service_specs(name = home_name, label = home_label)
    ser_resp = api.create_namespaced_service(namespace, home_body)
    print("Home service created. status = '%s'" % str(ser_resp.status))

    try:
        resp = api.read_namespaced_service(home_name, namespace)
    except ApiException as e:
        print("Exception Occurred")
    
    service_ips['home'] = resp.spec.cluster_ip
    home_ip = service_ips['home']

    for i in nodes:

        """
            Generate the yaml description of the required service for each task
        """
        if i != 'home':
            pod_name = app_name+'-controller'+i
            pod_label = app_name+'-controller'+i
            body = write_decoupled_pricing_circe_service_specs(name = pod_name, label = pod_label)

            # Call the Kubernetes API to create the service
    
            try:
                ser_resp = api.create_namespaced_service(namespace, body)
                print("Service created. status = '%s'" % str(ser_resp.status))
                print(i)
                resp = api.read_namespaced_service(pod_name, namespace)
            except ApiException as e:
                print("Exception Occurred")

            # print resp.spec.cluster_ip
            service_ips[i] = resp.spec.cluster_ip
            nexthost_ips = nexthost_ips + ':' + service_ips[i]
            nexthost_names = nexthost_names + ':' + i
            all_profiler_ips = all_profiler_ips + ':' + profiler_ips[i]

    home_profiler_ips = {}
    for key in homes:
        home_profiler_ips[key] = profiler_ips[key]

    home_profiler_str = ' '.join('{0}:{1}'.format(key, val) for key, val in sorted(home_profiler_ips.items()))

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
            pod_name = app_name+'-controller'+i
            label_name = app_name+'-controller'+i
            dep = write_decoupled_pricing_controller_worker_specs(name = pod_name, label = label_name, image = jupiter_config.WORKER_CONTROLLER_IMAGE,
                                             host = nodes[i][0], all_node = nexthost_names,
                                             all_node_ips = nexthost_ips,
                                             self_name=i,
                                             home_ip = home_ip,
                                             home_name = home_name,
                                             serv_ip = service_ips[i],
                                             profiler_ip = profiler_ips[i],
                                             child = jupiter_config.HOME_CHILD,
                                             all_profiler_ips = all_profiler_ips,
                                             home_profiler_ip = home_profiler_str)
            # # pprint(dep)
            # # Call the Kubernetes API to create the deployment
            resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
            print("Deployment created. status ='%s'" % str(resp.status))
            


    # have to somehow make sure that the worker nodes are on and working by this time
    
    while 1:
        if check_status_circe_controllers(app_name):
            break
        time.sleep(30)

    home_name = app_name+'-controllerhome'
    label_name = app_name+'-controllerhome'


    home_dep = write_decoupled_pricing_controller_home_specs(name = home_name, label = label_name,
                                image = jupiter_config.PRICING_HOME_CONTROLLER, 
                                host = jupiter_config.HOME_NODE, all_node = nexthost_names,
                                             all_node_ips = nexthost_ips,
                                             self_name = 'home',
                                             home_ip = home_ip,
                                             home_name = home_name,
                                             serv_ip = service_ips['home'],
                                             profiler_ip = profiler_ips['home'],
                                             all_profiler_ips = all_profiler_ips,
                                             home_profiler_ip = home_profiler_str,
                                             compute_home_ip = compute_service_ips['home'],
                                             child = jupiter_config.HOME_CHILD,
                                             app_name = app_name,
                                             app_option =jupiter_config.APP_OPTION)
    resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
    print("Home deployment created. status = '%s'" % str(resp.status))

    print('Successfully deploy CIRCE dispatcher')
    # if jupiter_config.BOKEH == 3:
    #     latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(nodes)+len(homes),len(dag))
    #     end_time = time.time()
    #     msg = 'CIRCE decoupled deployend %f \n'%(end_time)
    #     write_file(latency_file,msg)
    #     deploy_time = end_time - start_time
    #     print('Time to deploy CIRCE '+ str(deploy_time))

def k8s_decoupled_pricing_compute_scheduler(dag_info , profiler_ips, execution_ips,app_name):
    """
    This script deploys CIRCE in the system. 
    
    Args:
        dag_info : DAG info and mapping
        profiler_ips : IPs of network profilers
        execution_ips : IP of execution profilers 
        app_name (str): application name
    """
    jupiter_config.set_globals()
    
    sys.path.append(jupiter_config.CIRCE_PATH)

    global configs, taskmap, path1

    path1 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes = utilities.k8s_get_nodes_worker(path1)

    print('Starting to deploy decoupled CIRCE dispatcher')
    # if jupiter_config.BOKEH == 3:
    #     latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(nodes)+len(homes),len(dag))
    #     start_time = time.time()
    #     msg = 'CIRCE decoupled deploystart %f \n'%(start_time)
    #     write_file(latency_file,msg)


    configs = json.load(open(jupiter_config.APP_PATH+ 'scripts/config.json'))
    taskmap = configs["taskname_map"]
    executionmap = configs["exec_profiler"]


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
    service_ips = {}; #list of all service IPs including home and task controllers
    computing_service_ips = {}
    all_profiler_ips = ''
    all_profiler_nodes = ''
    

    print('-------- First create the home node service')
    """
        First create the home node's service.
    """

    for key in homes:
        all_profiler_ips = all_profiler_ips + ':'+ profiler_ips[key]
        all_profiler_nodes = all_profiler_nodes +':'+ key
        home_name =app_name+"-"+key
        home_body = write_decoupled_pricing_circe_compute_service_specs(name = home_name)
        ser_resp = api.create_namespaced_service(namespace, home_body)
        print("Home service created. status = '%s'" % str(ser_resp.status))

        try:
            resp = api.read_namespaced_service(home_name, namespace)
        except ApiException as e:
            print("Exception Occurred")

        service_ips[key] = resp.spec.cluster_ip

    """
        Iterate through the list of tasks and run the related k8 deployment, replicaset, pod, and service on the respective node.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g., 
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
    """ 
    print('-------- Create computing nodes service')

    """
        Create computing nodes' service
    """

    for node in nodes:
 
        """
            Generate the yaml description of the required service for each computing node
        """

        
        pod_name = app_name+"-"+node
        body = write_decoupled_pricing_circe_compute_service_specs(name = pod_name)

        # Call the Kubernetes API to create the service
        ser_resp = api.create_namespaced_service(namespace, body)
        print("Service created. status = '%s'" % str(ser_resp.status))
    
        try:
            resp = api.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            print("Exception Occurred")

        computing_service_ips[node] = resp.spec.cluster_ip
        all_profiler_ips = all_profiler_ips + ':' + profiler_ips[node]
        all_profiler_nodes = all_profiler_nodes + ':' + node

    all_computing_ips = ':'.join(computing_service_ips.values())
    all_computing_nodes = ':'.join(computing_service_ips.keys())


    """
    Start circe
    """

    print('---------  Start computing nodes')
    """
        Start computing nodes
    """

    home_nodes = {}
    for key in homes:
        home_nodes[key] = service_ips[key]

    home_nodes_str = ' '.join('{0}:{1}'.format(key, val) for key, val in sorted(home_nodes.items()))

    for i in nodes:
        
        """
            We check whether the node is a home / master.
            We do not run the controller on the master.
        """

        """
            Generate the yaml description of the required deployment for WAVE workers
        """
        pod_name = app_name+"-"+i
        dep = write_decoupled_circe_compute_worker_specs(name = pod_name, label =  pod_name, image = jupiter_config.WORKER_COMPUTE_IMAGE,
                                         host = nodes[i][0], node_name = i,
                                         # all_node = all_node,
                                         # all_node_ips = all_node_ips,
                                         all_computing_nodes = all_computing_nodes,
                                         all_computing_ips = all_computing_ips,
                                         self_ip = computing_service_ips[i],
                                         profiler_ip = profiler_ips[i],
                                         all_profiler_ips = all_profiler_ips,
                                         all_profiler_nodes = all_profiler_nodes,
                                         execution_home_ip = execution_ips['home'],
                                         home_node_ip = home_nodes_str,
                                         child = jupiter_config.HOME_CHILD)
        #pprint(dep)
        # # Call the Kubernetes API to create the deployment
        resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
        print("Deployment created. status ='%s'" % str(resp.status))


    while 1:
        if check_status_circe_compute(app_name):
            break
        time.sleep(30)

    print('-------- Start home node')

    for key in homes:
        home_name =app_name+"-" + key
        home_dep = write_decoupled_circe_compute_home_specs(name=home_name,image = jupiter_config.PRICING_HOME_COMPUTE, 
                                    host = jupiter_config.HOME_NODE, 
                                    child = jupiter_config.HOME_CHILD,
                                    child_ips = service_ips.get(jupiter_config.HOME_CHILD), 
                                    all_computing_nodes = all_computing_nodes,
                                    all_computing_ips = all_computing_ips,
                                    appname = app_name,
                                    appoption = jupiter_config.APP_OPTION,
                                    home_node_ip = home_nodes_str,
                                    profiler_ip= profiler_ips[key],
                                    all_profiler_ips = all_profiler_ips,
                                    all_profiler_nodes = all_profiler_nodes,
                                    dir = '{}')
        resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
        print("Home deployment created. status = '%s'" % str(resp.status))

    pprint(service_ips)
    return service_ips

def k8s_decoupled_pricing_circe_scheduler(dag_info , profiler_ips, execution_ips,app_name):
    compute_service_ips = k8s_decoupled_pricing_compute_scheduler(dag_info , profiler_ips, execution_ips,app_name)
    k8s_decoupled_pricing_controller_scheduler(profiler_ips,app_name,compute_service_ips)