__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "1.0"

import sys
sys.path.append("../../../")
import time
import os
from os import path
from multiprocessing import Process
import yaml
from kubernetes import client, config
from pprint import *
import jupiter_config
from kubernetes.client.rest import ApiException
import logging
from pathlib import Path
import shutil

logging.basicConfig(level = logging.DEBUG)

def k8s_read_dag(dag_info_file):
  """read the dag from the file input
  
  Args:
      dag_info_file (str): path of DAG file
  
  Returns:
      dict: DAG information 
  """
  dag_info=[]
  config_file = open(dag_info_file,'r')
  dag_size = int(config_file.readline())

  dag={}
  for i, line in enumerate(config_file, 1):
      dag_line = line.strip().split(" ")
      if i == 1:
          dag_info.append(dag_line[0])
      dag.setdefault(dag_line[0], [])
      for j in range(1,len(dag_line)):
          dag[dag_line[0]].append(dag_line[j])
      if i == dag_size:
          break

  dag_info.append(dag)
  print(dag_info)
  return dag_info

def k8s_get_all_elements(node_info_file):
  """read the node info from the file input
  
  Args:
      node_info_file (str): path of ``node.txt``
  
  Returns:
      dict: node information 
  """
  nodes = {}
  homes = {}
  datasources = {}
  datasinks ={}
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      if node_line[0].startswith('home'): 
        homes.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
          homes[node_line[0]].append(node_line[i])
      elif node_line[0].startswith('datasource'):
        datasources.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
          datasources[node_line[0]].append(node_line[i])
      elif node_line[0].startswith('datasink'):
        datasinks.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
          datasinks[node_line[0]].append(node_line[i])
      else:
        nodes.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
            nodes[node_line[0]].append(node_line[i])
  return nodes, homes,datasources,datasinks

def extract_log(namespace,label):
  k8s_apps_v1 = client.AppsV1Api()
  v1_delete_options = client.V1DeleteOptions()
  core_v1_api = client.CoreV1Api()
  resp = core_v1_api.list_namespaced_pod(namespace, label_selector = label)
    # if a pod is running just delete it
  if resp.items:
      a=resp.items[0]
      if a.status.phase != "Running":
          logging.debug("Pod Not Running %s", key)
          logging.debug(label)
      else:
          logging.debug('Pod information :')
          pod_name = resp.items[0].metadata.name
          file_name = os.path.join(log_folder,pod_name.split('-')[1])
          cmd = 'kubectl logs -n%s %s > %s' %(namespace,pod_name,file_name)
          os.system(cmd)
def extract_log_circe(log_folder):
    """
    This function logging.debugs out all the tasks that are not running.
    If all the tasks are running: return ``True``; else return ``False``.
    """

    jupiter_config.set_globals()

    path1 = jupiter_config.APP_PATH + 'configuration.txt'
    dag_info = k8s_read_dag(path1)
    dag = dag_info[1]
    app_name = jupiter_config.APP_OPTION+'1'

    path2 = jupiter_config.HERE + 'nodes.txt'
    nodes, homes,datasources,datasinks = k8s_get_all_elements(path2)

    logging.debug(dag)
    logging.debug(app_name)



    sys.path.append(jupiter_config.CIRCE_PATH)
    """
        This loads the kubernetes instance configuration.
        In our case this is stored in admin.conf.
        You should set the config file path in the jupiter_config.py file.
    """
    config.load_kube_config(config_file = jupiter_config.KUBECONFIG_PATH)
    namespace = jupiter_config.DEPLOYMENT_NAMESPACE
    logging.debug(namespace)


    # We have defined the namespace for deployments in jupiter_config

    # Get proper handles or pointers to the k8-python tool to call different functions.
    k8s_apps_v1 = client.AppsV1Api()
    v1_delete_options = client.V1DeleteOptions()
    core_v1_api = client.CoreV1Api()

    for key,value in dag.items():
        logging.debug(key)
        label = "app=" + app_name+'-'+key
        extract_log(namespace,label)


    label = "app=" + app_name+'-home'
    extract_log(namespace,label)

    for datasource in datasources:
      logging.debug(datasource)
      label = "app=" + app_name+'-stream'+datasource
      extract_log(namespace,label)




if __name__ == '__main__':
    log_folder = 'circe11default'
    if os.path.exists(log_folder):
        shutil.rmtree(log_folder)
    os.mkdir(log_folder)
    extract_log_circe(log_folder)
