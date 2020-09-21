__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,  Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")

import time
import os
from os import path
from multiprocessing import Process
import yaml
from kubernetes import client, config
from pprint import *
import json
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException

from write_exec_service_specs import *
from write_exec_specs import *
import utilities

import sys, json
sys.path.append("../")
import jupiter_config




def check_status_exec_profiler(app_name):
    """
    This function prints out all the tasks that are not running.
    If all the tasks are running: return ``True``; else return ``False``.
    """
    jupiter_config.set_globals()    

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    dag_info = utilities.k8s_read_config(path1)
    dag = dag_info[1]

    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)


    # We have defined the namespace for deployments in jupiter_config
    namespace = jupiter_config.EXEC_NAMESPACE

    # Get proper handles or pointers to the k8-python tool to call different functions.
    extensions_v1_beta1_api = client.ExtensionsV1beta1Api()
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
    result = True
    for key, value in dag.items():
        # First check if there is a deployment existing with
        # the name = key in the respective namespac    # Check if there is a replicaset running by using the label app={key}
        # The label of kubernets are used to identify replicaset associate to each task
        label = "app=" + app_name + "-"+key
        resp = None
        if taskmap[key][1] == False:

            resp = core_v1_api.list_namespaced_pod(namespace, label_selector = label)
            # if a pod is running just delete it
            if resp.items:
                a=resp.items[0]
                if a.status.phase != "Running":
                    print("Pod ", key, "status:",a.status.phase)
                    result = False

            # print("Pod Deleted. status='%s'" % str(del_resp_2.status))

    if result:
        print("All systems GOOOOO!!")
    else:
        print("Wait before trying again!!!!!!")
    return result

def check_status_exec_profiler_workers(app_name):
    """
    This function prints out all the workers that are not running.
    If all the workers are running: return ``True``; else return ``False``.
    """

    jupiter_config.set_globals()
    
    path1 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes = utilities.k8s_get_nodes_worker(path1)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    namespace = jupiter_config.EXEC_NAMESPACE


    # We have defined the namespace for deployments in jupiter_config

    # Get proper handles or pointers to the k8-python tool to call different functions.
    extensions_v1_beta1_api = client.ExtensionsV1beta1Api()
    v1_delete_options = client.V1DeleteOptions()
    core_v1_api = client.CoreV1Api()

    result = True
    for key in nodes:

        if key.startswith('node'):
            # First check if there is a deployment existing with
            # the name = key in the respective namespac    # Check if there is a replicaset running by using the label app={key}
            # The label of kubernets are used to identify replicaset associate to each task
            label = "app=" + app_name + "-" + key + "exec_profiler"

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

def write_file(filename,message):
    with open(filename,'a') as f:
        f.write(message)

def k8s_exec_scheduler(app_name):
    """
        This script deploys execution profiler in the system. 
    """


    
    jupiter_config.set_globals()

    global configs, taskmap, path1, path2
    
    configs = json.load(open(jupiter_config.APP_PATH+ 'scripts/config.json'))
    taskmap = configs["taskname_map"]

    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    path2 = jupiter_config.HERE + 'nodes.txt'

    dag_info = utilities.k8s_read_dag(path1)
    nodes, homes = utilities.k8s_get_nodes_worker(path2)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)

    """
        We have defined the namespace for deployments in jupiter_config
    """
    namespace = jupiter_config.EXEC_NAMESPACE

    """
        Get proper handles or pointers to the k8-python tool to call different functions.
    """
    api = client.CoreV1Api()
    k8s_beta = client.ExtensionsV1beta1Api()

    #get DAG and home machine info
    first_task = jupiter_config.HOME_CHILD
    dag = dag_info[1]
    # hosts
    service_ips = {}; #list of all service IPs





    print('Starting to deploy execution profiler')
    # if jupiter_config.BOKEH == 3:
    #     latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(nodes)+len(homes),len(dag))
    #     start_time = time.time()
    #     msg = 'Executionprofiler deploystart %f \n'%(start_time)
    #     write_file(latency_file,msg)

    """
        First create the home node's service.
    """

    home_name = app_name + '-home'
    home_body = write_exec_service_specs_home(name = home_name)

    ser_resp = api.create_namespaced_service(namespace, home_body)
    print("Home service created. status = '%s'" % str(ser_resp.status))

    try:
        resp = api.read_namespaced_service(home_name, namespace)
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
        pod_name = app_name+'-'+task
        if taskmap[key][1] == False:
            body = write_exec_service_specs_home(name = pod_name)

            # Call the Kubernetes API to create the service
            ser_resp = api.create_namespaced_service(namespace, body)
            print("Service created. status = '%s'" % str(ser_resp.status))

            try:
                resp = api.read_namespaced_service(pod_name, namespace)
            except ApiException as e:
                print("Exception Occurred")

            # print resp.spec.cluster_ip
            service_ips[task] = resp.spec.cluster_ip
        else:
            service_ips[task] = service_ips['home']

    all_node_ips = ':'.join(service_ips.values())
    all_node = ':'.join(service_ips.keys())
    print(all_node)

    
    
    allprofiler_ips =''
    allprofiler_names = ''

    for i in nodes:

        """
            Generate the yaml description of the required service for each task
        """
        if i.startswith('node'):
            pod_name = app_name+'-'+i
            body = write_exec_service_specs(name = pod_name, label = pod_name + "exec_profiler")

            # Call the Kubernetes API to create the service

            try:
                ser_resp = api.create_namespaced_service(namespace, body)
                print("Service created. status = '%s'" % str(ser_resp.status))
                print(i)
                resp = api.read_namespaced_service(pod_name, namespace)
            except ApiException as e:
                print("Exception Occurred")

            # print resp.spec.cluster_ip
            allprofiler_ips = allprofiler_ips + ':' + resp.spec.cluster_ip
            allprofiler_names = allprofiler_names + ':' + i

    """
    All services have started for CIRCE and deployment is yet to begin
    In the meantime, start dft_coded_detector services and their deployments
    """

    """
    Start circe
    """
    for key, value in dag.items():
        task = key
        nexthosts = ''
        next_svc = ''
        pod_name = app_name+'-'+task

        """
            We inject the host info for the child task via an environment variable valled CHILD_NODES to each pod/deployment.
            We perform it by concatenating the child-hosts via delimeter ':'
            For example if the child nodes are k8node1 and k8node2, we will set CHILD_NODES=k8node1:k8node2
            Note that the k8node1 and k8node2 in the example are the unique node ids of the kubernets cluster nodes.
        """
        inputnum = str(value[0])
        flag = str(value[1])
        nexthosts = nexthosts + 'test'

        for i in range(2, len(value)):
            if i != 2:
                next_svc = next_svc + ':'
            next_svc = next_svc + str(service_ips.get(value[i]))
        # print("NEXT HOSTS")
        # print(nexthosts)
        # print("NEXT SVC")
        # print(next_svc)

        if taskmap[key][1] == False:
            #Generate the yaml description of the required deployment for each task
            # TODO-check
            dep = write_exec_specs_non_dag_tasks(flag = str(flag), inputnum = str(inputnum), name = pod_name, node_name = task,
                image = jupiter_config.WORKER_IMAGE, child = nexthosts,
                child_ips = next_svc,
                task_name = task,
                home_node_ip = service_ips.get("home"),
                own_ip = service_ips[key],
                all_node = all_node,
                all_node_ips = all_node_ips)
            pprint(dep)


            # # Call the Kubernetes API to create the deployment
            resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
            print("Deployment created. status = '%s'" % str(resp.status))

    for i in nodes:

        """
            We check whether the node is a scheduler.
            Since we do not run any task on the scheduler, we donot run any profiler on it as well.
        """

        """
            Generate the yaml description of the required deployment for the profiles
        """
        if i.startswith('node'):
            pod_name = app_name+'-'+i
            dep = write_exec_specs(name = pod_name, label = pod_name + "exec_profiler", node_name = i, image = jupiter_config.EXEC_WORKER_IMAGE,
                                             host = nodes[i][0], home_node_ip = service_ips['home'],
                                             all_node = all_node,all_node_ips = all_node_ips)
            # # Call the Kubernetes API to create the deployment
            resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
            print("Deployment created. status ='%s'" % str(resp.status))

    """
        Check if all the tera detectors are running
    """
    while 1:
        if check_status_exec_profiler(app_name):
            break
        time.sleep(30)

    while 1:
        if check_status_exec_profiler_workers(app_name):
            break
        time.sleep(30)
    
    task = 'home'
    key = 'home'
    home_name = app_name+'-home'
    home_dep = write_exec_specs_home_control(flag = str(flag), inputnum = str(inputnum),
            name = home_name, node_name = home_name,
            task_name = task,
            image = jupiter_config.EXEC_HOME_IMAGE, child = nexthosts,
            child_ips = next_svc, host = jupiter_config.HOME_NODE, dir = '{}',
            home_node_ip = service_ips.get("home"),
            own_ip = service_ips[key],
            all_node = all_node,
            all_node_ips = all_node_ips,
            allprofiler_ips = allprofiler_ips,
            allprofiler_names = allprofiler_names)

    resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
    print("Home deployment created. status = '%s'" % str(resp.status))

    print('Successfully deploy execution profiler ')
    # if jupiter_config.BOKEH == 3:
    #     end_time = time.time()
    #     msg = 'Executionprofiler deployend %f \n'%(end_time)
    #     write_file(latency_file,msg)
    #     deploy_time = end_time - start_time
    #     print('Time to deploy execution profiler '+ str(deploy_time))

    return(service_ips)

if __name__ == '__main__':
    jupiter_config.set_globals() 
    app_name = jupiter_config.APP_OPTION
    k8s_exec_scheduler(app_name)
