__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar, Jason A Tran, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import time
from kubernetes import client, config
from pprint import *
import json

from kubernetes.client.rest import ApiException
import k8s_spec.service
import k8s_spec.deployment
from jupiter_utils import app_config_parser
import utilities
import logging

import sys
sys.path.append("../")
import jupiter_config

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def check_workers_running(app_config, namespace):
    """Checks if all worker tasks are up and running.

    Arguments:
        app_config {app_config_parser.AppConfig} -- app config objectj
        namespace {string} -- k8s namespace of execution profiler
    
    Returns:
        bool -- True if all workers are running, False if not.
    """
    # Load kube config before executing k8s client API calls.
    config.load_kube_config(config_file=jupiter_config.get_kubeconfig())
    k8s_apps_v1 = client.AppsV1Api()
    core_v1_api = client.CoreV1Api()

    result = True
    for node in app_config.node_list():
        if node.startswith('home'):
            # ignore checking on home status
            continue

        label = app_config.app_name + '-' + node + "exec_profiler"

        resp = core_v1_api.list_namespaced_pod(namespace, label_selector=label)
        # if a pod is running just delete it
        if resp.items:
            a = resp.items[0]
            if a.status.phase != "Running":
                log.debug("Execution Profiler pod not yet running on {}".format(node))
                result = False

    if result is True:
        log.info("All execution profiler workers successfully running.")

    return result

def write_file(filename, message):
    with open(filename, 'a') as f:
        f.write(message)

def main():
    # Parse app's app_config.yaml
    app_config = app_config_parser.AppConfig(jupiter_config.get_abs_app_dir(),
                                             jupiter_config.APP_NAME)
    namespace = app_config.namespace_prefix() + "-exec"

    # Load kube config before executing k8s client API calls.
    config.load_kube_config(config_file=jupiter_config.get_kubeconfig())
    api = client.CoreV1Api()
    k8s_apps_v1 = client.AppsV1Api()

    if jupiter_config.BOKEH == 3:
        log.critical("config processing changed, bokeh use needs fixing!")
        sys.exit(1)
        latency_file = utilities.prepare_stat_path(nodes, homes, dag)
        start_time = time.time()
        msg = 'Execution profiler deploystart %f \n'%(start_time)
        write_file(latency_file,msg)

    """
    Create k8s service for the home task. This task will signal profiling for
    all the execution profiler workers and collect results. K8s services exposes
    ports of pods to the entire k8s cluster. This does not launch pods.
    """
    home_svc_name = app_config.app_name + "-home"
    home_svc_spec = k8s_spec.service.generate(
        name=home_svc_name,
        port_mappings=jupiter_config.k8s_service_port_mappings()
    )
    resp = api.create_namespaced_service(namespace, home_svc_spec)
    log.debug("Home service created. status = '%s'" % str(resp.status))

    try:
        resp = api.read_namespaced_service(home_svc_name, namespace)
    except ApiException as e:
        log.error("Unable to read namespaced service")
        sys.exit(1)

    home_node_ip = resp.spec.cluster_ip

    """
    Create k8s service for all execution profiler workers. There is one worker
    per "worker_tasks" in the app's app_config.yaml. This service exposes the
    ports of the pods to the entire k8s cluster. This does not launch pods.
    """
    # to be injected into environment variables
    all_profiler_ips = []
    all_profiler_names = []

    for node in app_config.node_list():
        if node.startswith('home'):
            # skip scheduling tasks on the home node
            continue

        pod_name = app_config.app_name + '-' + node
        spec = k8s_spec.service.generate(
            name=pod_name, 
            port_mappings=jupiter_config.k8s_service_port_mappings()
        )

        try:
            resp = api.create_namespaced_service(namespace, spec)
            log.debug("Service created. status = '%s'" % str(resp.status))
            resp = api.read_namespaced_service(pod_name, namespace)
        except ApiException as e:
            log.error("Unable to create service for {}".format(pod_name))
            sys.exit(1)

        all_profiler_ips.append(resp.spec.cluster_ip)
        all_profiler_names.append(node)

    all_profiler_ips = ':'.join(all_profiler_ips)
    all_profiler_names = ':'.join(all_profiler_names)

    """
    Create k8s deployments for each worker task. Then, deploy it on the k8s
    cluster.
    """
    for node, host in app_config.node_list().items():
        if node.startswith('home'):
            # do not deploy pods on home yet. will be done afterwards. 
            continue

        pod_name = app_config.app_name + '-' + node
        spec = k8s_spec.deployment.generate(
            name=pod_name, 
            label=pod_name,
            image=app_config.get_exec_worker_tag(),
            host=host,
            port_mappings=jupiter_config.k8s_deployment_port_mappings(),
            # inject any arbitrary environment variables here
            env_vars= {
                "NODE_NAME": node,
                "HOME_NODE_IP": home_node_ip,
                "ALL_PROFILER_IPS": all_profiler_ips,
                "ALL_PROFILER_NAMES": all_profiler_names
            }
        )
        # # Call the Kubernetes API to create the deployment
        resp = k8s_apps_v1.create_namespaced_deployment(body=spec, namespace=namespace)
        log.debug("Deployment created. status ='%s'" % str(resp.status))

    # check if worker deployment pods are running
    while check_workers_running(app_config, namespace) is False:
        log.debug("Execution profiler worker pods still deploying, waiting...")
        time.sleep(30)
    
    """
    Create k8s deployment for home task and deploy it.
    """
    home_depl_spec = k8s_spec.deployment.generate(
        name=app_config.app_name + "-home", 
        label=app_config.app_name + "-home",
        image=app_config.get_exec_home_tag(), 
        host=app_config.home_host(), 
        port_mappings=jupiter_config.k8s_deployment_port_mappings(),
        env_vars={
            "NODE_NAME": "home",
            "HOME_NODE_IP": home_node_ip,
            "ALL_PROFILER_IPS": all_profiler_ips,
            "ALL_PROFILER_NAMES": all_profiler_names
        }
    )

    resp = k8s_apps_v1.create_namespaced_deployment(body=home_depl_spec, namespace=namespace)
    log.debug("Home deployment created. status = '%s'" % str(resp.status))

    if jupiter_config.BOKEH == 3:
        log.critical("config processing changed, bokeh use needs fixing!")
        sys.exit(1)
        end_time = time.time()
        msg = 'Executionprofiler deployed %f \n'%(end_time)
        write_file(latency_file,msg)
        deploy_time = end_time - start_time
        log.debug('Time to deploy execution profiler '+ str(deploy_time))

    log.info('Successfully deployed execution profiler.')

if __name__ == '__main__':
    main()
