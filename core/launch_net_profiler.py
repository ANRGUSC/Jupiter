__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
from kubernetes import client, config
import os
from pprint import *
from kubernetes.client.rest import ApiException
from kubernetes.client.apis import core_v1_api
import sys
sys.path.append("../")
import jupiter_config
import k8s_spec.service
import k8s_spec.deployment
from jupiter_utils import app_config_parser
import utilities
import logging

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
    for node in app_config.node_map():
        if node.startswith('home'):
            # ignore checking on home status
            continue

        label = app_config.app_name + '-' + node 

        resp = core_v1_api.list_namespaced_pod(namespace, label_selector=label)
        # if a pod is running just delete it
        if resp.items:
            a = resp.items[0]
            if a.status.phase != "Running":
                log.debug("Execution Profiler pod not yet running on {}".format(node))
                result = False

    if result is True:
        log.info("All drupe profiler workers successfully running.")

    return result

def write_file(filename,message,mode):
    with open(filename,mode) as f:
        f.write(message)

def main():
    """
        Deploy DRUPE in the system.
    """



    # Parse app's app_config.yaml
    app_config = app_config_parser.AppConfig(jupiter_config.get_abs_app_dir())
    namespace = app_config.namespace_prefix() + "-profiler"
    os.system(f"kubectl create namespace {namespace}")

    # Load kube config before executing k8s client API calls.
    config.load_kube_config(config_file=jupiter_config.get_kubeconfig())
    api = client.CoreV1Api()
    k8s_apps_v1 = client.AppsV1Api()


    """
        This loads the task graph and node list
    """

    logging.debug('Starting to deploy DRUPE')
    if jupiter_config.BOKEH == 3:
        latency_file = utilities.prepare_stat_path(node_list,homes,dag)
        start_time = time.time()
        msg = 'DRUPE deploystart %f \n'%(start_time)
        write_file(latency_file,msg,'w')


    all_profiler_map = dict()

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
    all_profiler_map['home'] = resp.spec.cluster_ip

    logging.debug('Home Profilers were created successfully!')

    all_profiler_ips = []
    all_profiler_names = []

    for node in app_config.node_map():
        """
            Generate the yaml description of the required service for each task
        """
        if node.startswith('home'):
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
        all_profiler_map[node] = resp.spec.cluster_ip

    all_profiler_ips = ':'.join(all_profiler_ips)
    all_profiler_names = ':'.join(all_profiler_names)

    logging.debug('Worker Profilers were created successfully!')


    for node, host in app_config.node_map().items():
        if node.startswith('home'):
            # do not deploy pods on home yet. will be done afterwards.
            continue

        pod_name = app_config.app_name + '-' + node
        spec = k8s_spec.deployment.generate(
            name=pod_name,
            label=pod_name,
            image=app_config.get_drupe_worker_tag(),
            host=host,
            port_mappings=jupiter_config.k8s_deployment_port_mappings(),
            # inject any arbitrary environment variables here
            env_vars= {
                "NODE_NAME": node,
                "HOME_NODE_IP": home_node_ip,
                "ALL_NODE_IPS": all_profiler_ips,
                "ALL_NODE_NAMES": all_profiler_names,
                "NODE_IP":all_profiler_map[node]
            }
        )
        # # Call the Kubernetes API to create the deployment
        resp = k8s_apps_v1.create_namespaced_deployment(body=spec, namespace=namespace)
        log.debug("Deployment created. status ='%s'" % str(resp.status))


    # check if worker deployment pods are running
    while check_workers_running(app_config, namespace) is False:
        log.debug("DRUPE profiler worker pods still deploying, waiting...")
        time.sleep(30)

    """
    Create k8s deployment for home task and deploy it.
    """
    home_depl_spec = k8s_spec.deployment.generate(
        name=app_config.app_name + "-home",
        label=app_config.app_name + "-home",
        image=app_config.get_drupe_home_tag(),
        host=app_config.home_host(),
        port_mappings=jupiter_config.k8s_deployment_port_mappings(),
        env_vars={
            "NODE_NAME": "home",
            "HOME_NODE_IP": home_node_ip,
            "ALL_NODE_IPS": all_profiler_ips,
            "ALL_NODE_NAMES": all_profiler_names,
            "NODE_IP":all_profiler_map["home"]
        }
    )

    resp = k8s_apps_v1.create_namespaced_deployment(body=home_depl_spec, namespace=namespace)
    log.debug("Home deployment created. status = '%s'" % str(resp.status))



    pprint(all_profiler_map)
    logging.debug('Successfully deploy DRUPE ')
    if jupiter_config.BOKEH == 3:
        end_time = time.time()
        msg = 'DRUPE deployend %f \n'%(end_time)
        write_file(latency_file,msg,'a')
        deploy_time = end_time - start_time
        logging.debug('Time to deploy DRUPE '+ str(deploy_time))
    return(all_profiler_map)

if __name__ == '__main__':
    main()