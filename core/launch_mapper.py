__author__ = "Quynh Nguyen, Pradipta Ghosh,  Pranav Sakulkar,  Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"
"""Launch task mapper on kubernetes cluster

TODO: change behavior of this script according to which task mapper is used.
"""
import os
import subprocess
import sys
import time
import requests
import json
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import k8s_spec.service
import k8s_spec.deployment
import logging
from jupiter_utils import app_config_parser

sys.path.append("../")
import jupiter_config

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def setup_proxy(port):
    """Automatically setup the proxy port

    Args:
        port (int): port number
    """
    cmd = f"kubectl proxy -p {str(port)}"
    return subprocess.Popen(cmd, shell=True)


def concat_worker_names(app_config):
    """
        Concatenates node names from app_config.yaml separated by ':', except
        the one the home task is assigned to,
    """
    node_names = ""
    for name, k8s_host in app_config.node_map().items():
        node_names = f"{node_names}:{name}"
    for ds in app_config.get_datasources():
        node_names = f"{node_names}:{ds['name']}"
    return node_names.lstrip(':')


def drupe_worker_names_to_ips(app_config, core_v1_api):
    """
        Looks up DRUPE network profiler service IP addresses except for the
        home pod. Returns a string that represents a mapping of Jupiter node
        names (node_map in app_config.yaml) to ip addresses that are space
        separated. The format of the string is:

        "jupiter_node_name:ip_addr jupiter_node_name:ip_addr ..."
    """
    name_to_ip = ""
    namespace = app_config.namespace_prefix() + "-profiler"

    for name, host in app_config.node_map().items():
        svc_name = app_config.app_name + '-' + name
        try:
            resp = core_v1_api.read_namespaced_service(svc_name, namespace)
            name_to_ip = f"{name_to_ip} {name}:{resp.spec.cluster_ip}"
        except ApiException:
            log.error("Could not find drupe service IP")

    for ds in app_config.get_datasources():
        svc_name = app_config.app_name + '-' + ds['name']
        try:
            resp = core_v1_api.read_namespaced_service(svc_name, namespace)
            name_to_ip = f"{name_to_ip} {name}:{resp.spec.cluster_ip}"
        except ApiException:
            log.error("Could not find drupe service IP")

    return name_to_ip.lstrip(' ')


def lookup_home_ip(namespace_postfix, app_config, core_v1_api):
    namespace = app_config.namespace_prefix() + namespace_postfix
    svc_name = f"{app_config.app_name}-home"
    try:
        resp = core_v1_api.read_namespaced_service(svc_name, namespace)
    except ApiException:
        log.error("Could not find home IP")
        return

    return resp.spec.cluster_ip


if __name__ == '__main__':
    # Parse app's app_config.yaml
    app_config = app_config_parser.AppConfig(jupiter_config.get_abs_app_dir())
    namespace = app_config.namespace_prefix() + "-mapper"
    app_name = app_config.app_name
    os.system(f"kubectl create namespace {namespace}")

    # Load kube config before executing k8s client API calls.
    config.load_kube_config(config_file=jupiter_config.get_kubeconfig())

    # manually set proxy
    k8s_apps_v1 = client.AppsV1Api()
    core_v1_api = client.CoreV1Api()
    exec_prof_home_ip = lookup_home_ip("-exec", app_config, core_v1_api)

    log.info('Starting to deploy HEFT (a single home pod)')

    home_svc_name = app_name + "-home"
    spec = k8s_spec.service.generate(
        name=home_svc_name,
        port_mappings=jupiter_config.k8s_service_port_mappings()
    )
    resp = core_v1_api.create_namespaced_service(namespace, spec)
    log.debug("Home service created. status = '%s'" % str(resp.status))

    try:
        resp = core_v1_api.read_namespaced_service(home_svc_name, namespace)
    except ApiException:
        log.error("Unable to read namespaced service")
        sys.exit(1)

    exec_prof_home_ip = lookup_home_ip("-exec", app_config, core_v1_api)
    drupe_home_ip = lookup_home_ip("-profiler", app_config, core_v1_api)

    home_depl_spec = k8s_spec.deployment.generate(
        name=app_name + "-home",
        label=app_name + "-home",
        image=app_config.get_mapper_tag(),
        host=app_config.home_host(),
        port_mappings=jupiter_config.k8s_deployment_port_mappings(),
        env_vars={
            "NODE_NAME": "home",
            "HOME_NODE_IP": resp.spec.cluster_ip,
            "DRUPE_WORKER_IPS": drupe_worker_names_to_ips(app_config, core_v1_api),
            "WORKER_NODE_NAMES": concat_worker_names(app_config),
            "EXEC_PROF_HOME_IP": exec_prof_home_ip,
            "DRUPE_HOME_IP": drupe_home_ip,
            "TASK_MAPPER": app_config.task_mapper(),
        }
    )
    resp = k8s_apps_v1.create_namespaced_deployment(
        body=home_depl_spec,
        namespace=namespace
    )
    log.debug("HEFT home deployment created. status = '%s'" % str(resp.status))
    log.info('Successfully deployed HEFT')

    # Setup k8s proxy and retrieve mapping from HEFT pod
    proxy_proc = setup_proxy(jupiter_config.kubectl_proxy_heft())
    svc_port, _ = jupiter_config.flask_port_mapping()
    url = f"http://localhost:{8081}/api/v1/" \
          + f"namespaces/{namespace}/services/{app_name}-home:{svc_port}/proxy"
    log.info("Waiting for HEFT pod to boot...")
    time.sleep(10)
    while 1:
        try:
            r = requests.get(url)
            mapping = json.dumps(r.json(), indent=4)
            log.info(f"mapping:\n{mapping}")
            if len(mapping) != 0:
                if "status" not in mapping:
                    break
        except:
            log.debug("HEFT not finished, retry in 30 sec...")
            time.sleep(30)

    with open("mapping.json", 'w') as f:
        f.write(json.dumps(r.json(), indent=4))
        log.info("Wrote mapping to file mapping.json. Ready to launch CIRCE.")


    # TODO: print message talking about killing proxy
    proxy_proc.kill()
