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
import utilities
from kubernetes.client.rest import ApiException
    
 
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
        # print(key)
        # print(value)

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
                print(label)
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

def k8s_circe_scheduler(dag_info, temp_info, app_name):
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
    nodename_to_DNS = temp_info[3]
    first_task = dag_info[0]
    dag = dag_info[1]
    hosts = temp_info[2]
    
    for key in hosts:
        if len(hosts[key]) == 2:
            if hosts[key][0] != 'home':
                hosts[key][0] = hosts[key][0] + "-1"
        else:
            for i in range(len(hosts[key])):
                if i % 2 == 1:
                    continue
                else:
                    hosts[key][i] = hosts[key][i] + "-" + str(int(i/2 + 1))
                    
    print("hosts:")
    """
    example hosts:
    {'home': ['home', 'master'],
     'task0': ['task0-1', 'n2'],
     'task1': ['task1-1', 'n6', 'task1-2', 'n7'],
     'task2': ['task2-1', 'n3', 'task2-2', 'n4'],
     'task3': ['task3-1', 'n0'],
     'task4': ['task4-1', 'n1', 'task4-2', 'n5']}
     
    example DAG info:
    {'task0': ['1', 'true', 'task1', 'task2', 'task3'], 
     'task1': ['1', 'true', 'task4'], 
     'task2': ['1', 'true', 'task4'], 
     'task3': ['1', 'true', 'task4'], 
     'task4': ['3', 'true', 'home']} 
    """
    pprint(hosts)
    print('DAG info:')
    print(dag)
    task_number_of_parents = {}
    for key, val in dag.items():
        for i in range(2, len(val)):
            if val[i] not in task_number_of_parents:
                task_number_of_parents[val[i]] = 1
            else:
                task_number_of_parents[val[i]] += 1
    multi_parent_tasks = set()
    for task, num_parent in task_number_of_parents.items():
        if num_parent > 1:
            multi_parent_tasks.add(task)
    mpt = ""
    for task in multi_parent_tasks:
        mpt += task + ":"
    mpt = mpt.rstrip(':')    
    print("tasks with multiple parents")
    print(mpt)
    
    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes = utilities.k8s_get_nodes_worker(path2)

    print('Starting to deploy CIRCE dispatcher')
    if jupiter_config.BOKEH == 3:
        latency_file = '../stats/exp8_data/summary_latency/system_latency_N%d_M%d.log'%(len(nodes)+len(homes),len(dag))
        start_time = time.time()
        msg = 'CIRCE deploystart %f \n'%(start_time)
        write_file(latency_file,msg)

    service_ips = {}; #list of all service IPs

    # #     First create the home node's service.
    
    print('First create the home node service')
    home_name =app_name+"-home"
    home_body = write_circe_service_specs(name = home_name)
    
    try:
        ser_resp = api.create_namespaced_service(namespace, home_body)
        print("Home service created. status = '%s'" % str(ser_resp.status))
        resp = api.read_namespaced_service(home_name, namespace)
        service_ips['home'] = resp.spec.cluster_ip
    except ApiException as e:
        print(e)
        print("Exception Occurred")
        


    
    # print(resp.spec.cluster_ip)

    """
        Iterate through the list of tasks and run the related k8 deployment, replicaset, pod, and service on the respective node.
        You can always check if a service/pod/deployment is running after running this script via kubectl command.
        E.g., 
            kubectl get svc -n "namespace name"
            kubectl get deployement -n "namespace name"
            kubectl get replicaset -n "namespace name"
            kubectl get pod -n "namespace name"
        
        For the purpose of split, assign a pod for each task's replica
    """ 
    mapp = dag_info[2]
    # mapping from task name to its number of replicas
    # if one replica of a task, just taskX
    # if multiple, will be called taskX-1, taskX-2, ...
    # Assign independent pods for each task's replica
    replicas = {}
    all_tasks = []
    
    for key, value in mapp.items():
        if type(value) is list:
            for i in range(int(len(value)/2)):
                all_tasks.append(key)
        else:
            all_tasks.append(key)
            
    print('Create workers service')
    for task in all_tasks:
        nexthosts = ''
        if task not in replicas:
            replicas[task] = 1
        else:
            replicas[task] += 1
        """
            Generate the yaml description of the required service for each task
        """
        pod_name = app_name + "-" + task + "-" + str(replicas[task])
        body = write_circe_service_specs(name = pod_name)

        
    
        try:
            # Call the Kubernetes API to create the service
            ser_resp = api.create_namespaced_service(namespace, body)
            print("Service created. status = '%s'" % str(ser_resp.status))
            resp = api.read_namespaced_service(pod_name, namespace)
            # print resp.spec.cluster_ip
            service_ips[task+"-"+str(replicas[task])] = resp.spec.cluster_ip
        except ApiException as e:
            print(e)
            print("Exception Occurred")

    all_node_ips = ':'.join(service_ips.values())
    all_node = ':'.join(service_ips.keys())
    
    """
    All services have started for CIRCE and deployment is yet to begin
    """

    """
    Start circe
    """
    # key: task, value: a hashmap {key: node, value: portion}
    task_node_portion = {}
    for key in mapp:
        task_node_portion[key] = {}
    for key, val in mapp.items():
        if type(val) is list:
            i = 0
            while(i < len(val)):
                task_node_portion[key][val[i]] = val[i+1]
                i += 2
        else:
            task_node_portion[key][val] = 1.0
    
    task_nodename_portion = {}
    for key in task_node_portion:
        task_nodename_portion[key] = {}
    for key, val in task_node_portion.items():
        for subkey, subval in val.items():
            task_nodename_portion[key][nodename_to_DNS[subkey][0]] = subval
    task_nodename_portion['home'] = {}
    task_nodename_portion['home'][nodename_to_DNS['home'][0]] = 1.000
    
    for key, value in dag.items():
        for i in range(1, replicas[key]+1):
            task = key + '-' + str(i)
            nexthosts = ''
            next_svc = ''

            """
                We inject the host info for the child task via an environment variable valled CHILD_NODES to each pod/deployment.
                We perform it by concatenating the child-hosts via delimeter ':'
                For example if the child nodes are k8node1 and k8node2, we will set CHILD_NODES=k8node1:k8node2
                Note that the k8node1 and k8node2 in the example are the unique node ids of the kubernetes cluster nodes
                
                Example ENV for task0's pod:
                CHILD_NODES=task1:task2
                CHILD_NODES_IPS=10.103.170.159:10.110.186.67
                (Xiangchen comment: the 'node' here means task/pod, not cluster node)
                
                If a pod (task0) has multiple child (task1, task2), among them, task1 has 3 child replicas, task2 has just one,
                inject the ENV this way task1-1/{portion1}:task1-2/{portion2}:task1-3/{portion3}:task2-1/1.0
            """
            inputnum = str(value[0])
            flag = str(value[1])
                   
            for i in range(2,len(value)):
                child_hostnames = []
                child_hostportions = []
                if type(hosts[value[i]]) is list:
                    for j in range(len(hosts[value[i]])):
                        if j % 2 == 0:
                            child_hostnames.append(hosts[value[i]][j])
                        else:
                            child_hostportions.append(str(round(task_nodename_portion[value[i]][hosts[value[i]][j]] ,3)))
                    for k in range(len(child_hostnames)):
                        nexthosts = nexthosts + child_hostnames[k] + "/" + child_hostportions[k] + ":"
                        next_svc = next_svc + str(service_ips[child_hostnames[k]]) + "/" + child_hostportions[k] + ":"
                else:
                    nexthosts = nexthosts + str(hosts.get(value[i])[0]) + "-1/1.000:"
                    next_svc = next_svc + str(service_ips[hosts.get(value[i])]) + "-1/" + child_hostportions[k] + ":"
            
            nexthosts = nexthosts.rstrip(':')
            next_svc = next_svc.rstrip(':')
            pod_name = app_name+"-"+task
            #Generate the yaml description of the required deployment for each task
            node_name_here = hosts[task.split('-')[0]][int(task.split('-')[-1])*2-1]
            dep = write_circe_deployment_specs(name = pod_name, node_name = node_name_here,
                image = jupiter_config.WORKER_IMAGE, child = nexthosts, task_name=task,
                child_ips = next_svc, host = node_name_here, dir = '{}',
                home_node_ip = service_ips.get('home'),
                own_ip = service_ips[task],
                all_node = all_node,
                all_node_ips = all_node_ips,
                flag = str(flag), inputnum = str(inputnum), multi_parent_tasks=mpt)

            # # Call the Kubernetes API to create the deployment
            try:
                resp = k8s_beta.create_namespaced_deployment(body = dep, namespace = namespace)
                print("Deployment created")
                print("Deployment created. status = '%s'" % str(resp.status))
            except ApiException as e:
                print(e)

    while 1:
        print('Checking status CIRCE workers')
        if check_status_circe(dag,app_name):
            break
        time.sleep(30)
    
    # get a list of home child's (consider task0) replicas and portion
    entry_task = jupiter_config.HOME_CHILD
    tmp = hosts[entry_task]
    entry_nodeDNS_to_taskname = {}
    """
    tmp
    ['task0-1', 'ubuntu-s-1vcpu-2gb-nyc3-01', 'task0-2', 'ubuntu-s-1vcpu-2gb-sfo2-03', 'task0-3', 'ubuntu-s-1vcpu-2gb-sfo2-04']
    
    mapp
    {'task0': ['node1', 0.1296876493284042, 'node3', 0.48449175858909777, 'node6', 0.385820592082498], 
     'task1': ['node2', 0.6756664055262795, 'node5', 0.32433359447372045], 
     'task2': 'node7', 
     'task3': 'node4'}

    """
    print("MAPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP")
    print(mapp)
    child_spec = ""
    child_spec_ips = ""
    DNS_to_nodename = {}
    for key, val in nodename_to_DNS.items():
        DNS_to_nodename[val[0]] = key
    tmpmap = {}
    for i in range(len(tmp)):
        if i % 2 == 0:
            tmpmap[tmp[i]] = tmp[i+1]   
    for key, val in tmpmap.items():
        taskname = key
        nodeDNS = val
        nodename = DNS_to_nodename[nodeDNS]
        idx = mapp[entry_task].index(nodename)
        portion = str(round(mapp[entry_task][idx+1], 3)) if type(mapp[entry_task]) is list else '1.000'
        child_spec = child_spec + taskname + '/' + portion + ':'
        child_spec_ips = child_spec_ips + service_ips[taskname] + '/' + portion + ':'
    child_spec = child_spec.rstrip(':')
    child_spec_ips = child_spec_ips.rstrip(':')
    
    home_name =app_name+"-home"
    home_dep = write_circe_home_specs(name=home_name,image = jupiter_config.HOME_IMAGE, 
                                host = jupiter_config.HOME_NODE, 
                                child = child_spec,
                                child_ips = child_spec_ips, 
                                appname = app_name,
                                appoption = jupiter_config.APP_OPTION,
                                dir = '{}')

    try:
        resp = k8s_beta.create_namespaced_deployment(body = home_dep, namespace = namespace)
        print("Home deployment created")
        print("Home deployment created. status = '%s'" % str(resp.status))
    except ApiException as e:
        print(e)


    pprint(service_ips)
    print('Successfully deploy CIRCE dispatcher')
    if jupiter_config.BOKEH == 3:
        end_time = time.time()
        msg = 'CIRCE deployend %f \n'%(end_time)
        write_file(latency_file,msg)
        deploy_time = end_time - start_time
        print('Time to deploy CIRCE '+ str(deploy_time))

   
