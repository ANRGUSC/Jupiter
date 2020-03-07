__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")
import time
import os
from os import path
from multiprocessing import Process
from write_profiler_service_specs import *
from write_profiler_specs import *
from kubernetes import client, config
from pprint import *
import os
import jupiter_config
from kubernetes.client.rest import ApiException
import utilities 

def check_status_profilers():
    """Verify if all the network profilers have been deployed and UP in the system.
    """
    jupiter_config.set_globals()
    
    path1 = jupiter_config.HERE + 'nodes.txt'
    nodes = utilities.k8s_get_nodes(path1)

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    namespace = jupiter_config.PROFILER_NAMESPACE


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
        label = "app=" + key + "profiler"

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

def write_file(filename,message,mode):
    with open(filename,mode) as f:
        f.write(message)
def k8s_profiler_scheduler(): 
    """
        Deploy DRUPE in the system. 
    """
    


    jupiter_config.set_globals()


    """
        This loads the task graph and node list
    """
    home_ips = ''
    home_ids = ''
    nexthost_ips = ''
    nexthost_names = ''
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    path2 = jupiter_config.HERE + 'nodes.txt'
    dag_info = utilities.k8s_read_dag(path1)
    node_list, homes = utilities.k8s_get_nodes_worker(path2)
    
    dag = dag_info[1]

    print('Starting to deploy DRUPE')
    if jupiter_config.BOKEH == 3:
        try:
            os.mkdir('../stats/exp8_data/summary_latency/')
        except:
            print('Folder already existed')
        latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(node_list)+len(homes),len(dag))
        start_time = time.time()
        msg = 'DRUPE deploystart %f \n'%(start_time)
        write_file(latency_file,msg,'w')


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
    nodes = utilities.k8s_get_nodes(path2)
    service_ips = {}; 

    # get the list of nodes
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
    for i in nodes:
        if i.startswith('home'):
            home_body = write_profiler_service_specs(name = i, label = i + "profiler")
            ser_resp = api.create_namespaced_service(namespace, home_body)
            print("Home service created. status = '%s'" % str(ser_resp.status))
            try:
                resp = api.read_namespaced_service(i, namespace)
                service_ips[i] = resp.spec.cluster_ip
                home_ids = home_ids + ':' + i
                home_ips = home_ips + ':' + service_ips[i]
            except ApiException as e:
                print(e)
                print("Exception Occurred")
    
        
    print('Home Profilers were created successfully!')

    for i in nodes:

        """
            Generate the yaml description of the required service for each task
        """
        if i.startswith('home'):
            continue
        body = write_profiler_service_specs(name = i, label = i + "profiler")

        # Call the Kubernetes API to create the service

        try:
            ser_resp = api.create_namespaced_service(namespace, body)
            print("Service created. status = '%s'" % str(ser_resp.status))
            print(i)
            resp = api.read_namespaced_service(i, namespace)
        except ApiException as e:
            print(e)
            print("Exception Occurred")

        # print resp.spec.cluster_ip
        service_ips[i] = resp.spec.cluster_ip
        nexthost_ips = nexthost_ips + ':' + service_ips[i]
        nexthost_names = nexthost_names + ':' + i

    print('Worker Profilers were created successfully!')
    print(service_ips)
    print(nexthost_ips)
    print(nexthost_names)

    for i in nodes:
        
        """
            We check whether the node is a scheduler.
            Since we do not run any task on the scheduler, we donot run any profiler on it as well.
        """
        if i.startswith('home'):
            continue
        """
            Generate the yaml description of the required deployment for the profiles
        """
        dep = write_profiler_specs(name = i, label = i + "profiler", image = jupiter_config.PROFILER_WORKER_IMAGE,
                                         host = nodes[i][0], dir = '{}', all_node = nexthost_names,
                                         all_node_ips = nexthost_ips,
                                         serv_ip = service_ips[i],
                                         home_ips = home_ips,
                                         home_ids = home_ids)
        # # Call the Kubernetes API to create the deployment
        resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
        print("Deployment created. status ='%s'" % str(resp.status))
            
    while 1:
        if check_status_profilers():
            break
        time.sleep(30)

    for i in nodes:
        if i.startswith('home'):
            home_dep = write_profiler_specs(name = i, label = i+"profiler",
                                        image = jupiter_config.PROFILER_HOME_IMAGE, 
                                        host = jupiter_config.HOME_NODE, 
                                        dir = '{}', all_node = nexthost_names,
                                                     all_node_ips = nexthost_ips,
                                                     serv_ip = service_ips[i],
                                                     home_ips = home_ips,
                                                     home_ids = home_ids)
            resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
            print("Home deployment created. status = '%s'" % str(resp.status))

            pprint(service_ips)
    
    

    pprint(service_ips)
    print('Successfully deploy DRUPE ')
    if jupiter_config.BOKEH == 3:
        end_time = time.time()
        msg = 'DRUPE deployend %f \n'%(end_time)
        write_file(latency_file,msg,'a')
        deploy_time = end_time - start_time
        print('Time to deploy DRUPE '+ str(deploy_time))
    return(service_ips)

if __name__ == '__main__':
    k8s_profiler_scheduler()