__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar, Jason A Tran, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import k8s_spec.service
import k8s_spec.deployment
from jupiter_utils import app_config_parser
import logging
import json
import time

import sys
sys.path.append("../")
import jupiter_config

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def create_services(app_name, namespace, tasks, api, port_mappings):
    # *** Create Non-DAG Task Services ***
    task_to_ip = []
    for task in tasks:
        pod_name = app_name + '-' + task['name']
        spec = k8s_spec.service.generate(
            name=pod_name,
            port_mappings=port_mappings
        )

        try:
            resp = api.create_namespaced_service(namespace, spec)
            log.debug("Service created. status = '%s'" % str(resp.status))
            resp = api.read_namespaced_service(pod_name, namespace)
        except ApiException:
            log.error("Unable to create service for {}".format(pod_name))
            sys.exit(1)

        task_to_ip.append(f"{task['name']}:{resp.spec.cluster_ip}")

    # space separated mapping of task name to IP addr.
    # example: "task0:10.0.0.1 task1:10.0.0.2"
    return ' '.join(task_to_ip)

def check_dag_workers_running(app_config, namespace):
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

    for task in app_config.get_dag_task_names():
        label = "app="+app_config.app_name + '-' + task 
        resp = core_v1_api.list_namespaced_pod(namespace, label_selector=label)
        # if a pod is running just delete it
        if resp.items:
            a = resp.items[0]
            if a.status.phase != "Running":
                log.debug("Circe dag workers pod not yet running on {}".format(task))
                result = False

    if result is True:
        log.info("All drupe profiler workers successfully running.")

    return result

def check_nondag_workers_running(app_config, namespace):
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

    for task in app_config.get_nondag_tasks():
        label = "app="+app_config.app_name + '-' + task 
        resp = core_v1_api.list_namespaced_pod(namespace, label_selector=label)
        # if a pod is running just delete it
        if resp.items:
            a = resp.items[0]
            if a.status.phase != "Running":
                log.debug("Circe dag workers pod not yet running on {}".format(task))
                result = False

    if result is True:
        log.info("All drupe profiler workers successfully running.")

    return result


def launch_circe(task_mapping):
    # Parse app's app_config.yaml
    app_config = app_config_parser.AppConfig(jupiter_config.get_abs_app_dir())
    namespace = app_config.namespace_prefix() + "-circe"
    os.system(f"kubectl create namespace {namespace}")

    # Load kube config before executing k8s client API calls.
    config.load_kube_config(config_file=jupiter_config.get_kubeconfig())
    api = client.CoreV1Api()
    k8s_apps_v1 = client.AppsV1Api()

    # Compile port mappings for k8s services for Jupiter and the application
    svc_port_mappings = jupiter_config.k8s_service_port_mappings()

    try:
        for idx, mapping in enumerate(app_config.port_mappings()):
            svc, docker = mapping.split(':')
            svc_port_mappings.append({
                "name": f"custom{idx}",
                "port": int(svc),
                "targetPort": int(docker)
            })
    except Exception as e:
        logging.debug('No application port mappings')
    # Compile port mappings for k8s deployments for Jupiter and the application
    depl_port_mappings = jupiter_config.k8s_deployment_port_mappings()

    try:
        for idx, mapping in enumerate(app_config.port_mappings()):
            svc, docker = mapping.split(':')
            depl_port_mappings.append({
                "name": f"custom{idx}",
                "containerPort": int(docker)
            })
    except Exception as e:
        logging.debug('No application port mappings')

    # *** Create Home Task Service ***
    home_svc_name = app_config.app_name + "-home"
    home_svc_spec = k8s_spec.service.generate(
        name=home_svc_name,
        port_mappings=svc_port_mappings
    )
    resp = api.create_namespaced_service(namespace, home_svc_spec)
    log.debug("Home service created. status = '%s'" % str(resp.status))

    try:
        resp = api.read_namespaced_service(home_svc_name, namespace)
    except ApiException:
        log.error("Unable to read namespaced service")
        sys.exit(1)

    home_task_ip = resp.spec.cluster_ip

    # *** Create DAG Task Services ***
    task_to_ip_string = create_services(
        app_config.app_name,
        namespace,
        app_config.get_dag_tasks(),
        api,
        svc_port_mappings
    )

    # *** Create Non-DAG Task Services ***
    nondag_task_to_ip_string = create_services(
        app_config.app_name,
        namespace,
        app_config.get_nondag_tasks(),
        api,
        svc_port_mappings
    )

    # *** Create DAG Task Deployments ***
    # Each DAG task to be launched on nodes designated by task_mapping
    # (e.g., derived from "mapping.json" file). Node names in task_mapping will
    # be mapped to the k8s hostname as indicated in app_config.yaml.
    node_map = app_config.node_map()
    for task in app_config.get_dag_tasks():
        try:
            node = task_mapping[task['name']]
            k8s_hostname = node_map[node]
        except KeyError:
            log.fatal("Task missing in mapping file or node not in " +
                      "app_config.yaml. Clean up with delete_all_circe.py.")
            exit()

        pod_name = app_config.app_name + '-' + task['name']
        spec = k8s_spec.deployment.generate(
            name=pod_name,
            label=pod_name,
            image=app_config.get_circe_tag(),
            host=k8s_hostname,
            port_mappings=depl_port_mappings,
            # inject any arbitrary environment variables here
            env_vars={
                "MY_TASK_NAME": task['name'],
                "CIRCE_HOME_IP": home_task_ip,
                "CIRCE_TASK_TO_IP": task_to_ip_string,
                "CIRCE_NONDAG_TASK_TO_IP": nondag_task_to_ip_string,
            }
        )
        resp = k8s_apps_v1.create_namespaced_deployment(body=spec,
                                                        namespace=namespace)
        log.debug(f"DAG task deployment created. status={resp.status}")

    while check_dag_workers_running(app_config, namespace) is False:
        log.debug("CIRCE dag worker pods still deploying, waiting...")
        time.sleep(30)


    # *** Create Non-DAG Task Deployments ***
    for nondag_task in app_config.get_nondag_tasks():
        pod_name = app_config.app_name + '-' + nondag_task['name']
        spec = k8s_spec.deployment.generate(
            name=pod_name,
            label=pod_name,
            image=app_config.get_circe_tag(),
            host=nondag_task['k8s_host'],
            port_mappings=depl_port_mappings,
            # inject any arbitrary environment variables here
            env_vars={
                "MY_TASK_NAME": nondag_task['name'],
                "CIRCE_HOME_IP": home_task_ip,
                "CIRCE_TASK_TO_IP": task_to_ip_string,
                "CIRCE_NONDAG_TASK_TO_IP": nondag_task_to_ip_string,
            }
        )
        resp = k8s_apps_v1.create_namespaced_deployment(body=spec,
                                                        namespace=namespace)
        log.debug(f"Non-DAG task depl. created. status={resp.status}")

    while check_nondag_workers_running(app_config, namespace) is False:
        log.debug("CIRCE nondag worker pods still deploying, waiting...")
        time.sleep(30)

    # *** Create Home Task Deployment ***
    home_depl_spec = k8s_spec.deployment.generate(
        name=app_config.app_name + "-home",
        label=app_config.app_name + "-home",
        image=app_config.get_circe_tag(),
        host=app_config.home_host(),
        port_mappings=depl_port_mappings,
        env_vars={
            "MY_TASK_NAME": "home",
            "CIRCE_HOME_IP": home_task_ip,
            "CIRCE_TASK_TO_IP": task_to_ip_string,
            "CIRCE_NONDAG_TASK_TO_IP": nondag_task_to_ip_string,
        }
    )

    resp = k8s_apps_v1.create_namespaced_deployment(body=home_depl_spec,
                                                    namespace=namespace)
    log.debug(f"Home deployment created. status={resp.status}")
    log.info('CIRCE successfully deployed')


if __name__ == '__main__':
    if len(sys.argv) == 2:
        mapping_file = sys.argv[1]
    if len(sys.argv) == 1:
        log.info("No task mapping file arg, defaulting to \"mapping.json\"")
        mapping_file = "mapping.json"
    else:
        log.error("usage: python build_push_exec.py {task_mapping_file}")
        exit()

    # task_mapping should be a dictionary of task names to node names. Node
    # names are the keys under "node_map" in the app_config.yaml
    with open(mapping_file, 'r') as f:
        task_mapping = json.load(f)

    log.info("Launching tasks on kubernetes cluster...")
    launch_circe(task_mapping)
