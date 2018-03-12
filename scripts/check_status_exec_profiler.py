"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""
import sys, json
sys.path.append("../")
import jupiter_config
sys.path.append(jupiter_config.CIRCE_PATH)

from readconfig import k8s_read_config
import yaml
from kubernetes import client, config
from pprint import *
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException



def check_status_exec_profiler():
    configs = json.load(open(jupiter_config.APP_PATH+ 'scripts/config.json'))
    taskmap = configs["taskname_map"]

    """
        This loads the task graph
    """
    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = k8s_read_config(path1)
    dag = dag_info[1]

    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
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
        label = "app=" + key
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


if __name__ == '__main__':
    check_status_exec_profiler()