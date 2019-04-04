__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import yaml
import sys
sys.path.append("../")
import jupiter_config
import configparser

def add_ports(dep, app_specific_flag, *args):
  """Add information of ports for the application
  
  Args:
      dep (str): deployment service description
      app_specific_flag (boolean) : flag to add app specific ports
      args (list): List of app independent ports required by circe
  
  Returns:
      str: deployment service description with added port information for the application
  """
  jupiter_config.set_globals()

  INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
  config = configparser.ConfigParser()
  config.read(INI_PATH)

  dep['spec']['template']['spec']['containers'][0]['ports'] = []
  a = dep['spec']['template']['spec']['containers'][0]['ports']
  for i in args:
    a.append({'containerPort': int(i)})

  # Add app specific ports 
  if app_specific_flag == 1:
    for i in config['DOCKER_PORT']:
      a.append({'containerPort': int(config['DOCKER_PORT'][i])})

  return dep


template_home = """
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: {name}
spec:
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
      - name: {name}
        image: {image}
        imagePullPolicy: Always
        ports:
        - containerPort: {ssh_port}
        - containerPort: {flask_port}
        env:
        - name: CHILD_NODES
          value: {child}
        - name: CHILD_NODES_IPS
          value: {child_ips}
        - name: TASK
          value: home
      restartPolicy: Always
"""


def write_circe_home_specs(**kwargs):
    """
    This function genetares the description yaml for CIRCE
     
    In this case, call argument should be:
    
      -   image: {image}
      -   SSH Port: {ssh_port}
      -   Flask Port: {flask_port}
      -   CHILD_NODES_IPS: {child_ips}
      -   kubernetes.io/hostname: {host}
    
    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """

    jupiter_config.set_globals()

    INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    specific_yaml = template_home.format(ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)

    dep = yaml.load(specific_yaml)
    return dep


template_worker = """
apiVersion: extensions/v1beta1
kind: Deployment    
metadata:
  name: {name}
  labels:
    app: ssh
    purpose: dag-demo
spec:
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
      - name: {name}
        imagePullPolicy: Always
        image: {image}
        env:
        - name: FLAG
          value: {flag}
        - name: INPUTNUM
          value: {inputnum}
        - name: CHILD_NODES
          value: {child}
        - name: CHILD_NODES_IPS
          value: {child_ips}
        - name: TASK
          value: {task_name}
        - name: NODE_NAME
          value: {node_name}
        - name: HOME_NODE
          value: {home_node_ip}
        - name: OWN_IP
          value: {own_ip}
        - name: ALL_NODES
          value: {all_node}
        - name: ALL_NODES_IPS
          value: {all_node_ips}
      nodeSelector:
        kubernetes.io/hostname: {host}
      restartPolicy: Always
"""

def write_circe_deployment_specs(**kwargs):
    """
    This function genetares the deployment service description yaml for CIRCE
     
    In this case, call argument should be:
    
      -   app: {name}
      -   image: {image}
      -   containerPort: {ssh_port}
      -   FLAG: {flag}
      -   INPUTNUM: {inputnum}
      -   CHILD_NODES: {child}
      -   CHILD_NODES_IPS: {child_ips}
      -   NODE_NAME: {node_name}
      -   HOME_NODE: {home_node_ip}
      -   OWN_IP: {own_ip}
      -   ALL_NODES: {all_node}
      -   ALL_NODES_IPS: {all_node_ips}
      -   kubernetes.io/hostname: {host}
    
    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """

    # insert your values
    jupiter_config.set_globals()
    # for i in kwargs:
    print(kwargs)
    specific_yaml = template_worker.format(**kwargs)
    print(specific_yaml)
    dep = yaml.load(specific_yaml, Loader=yaml.BaseLoader)
    
    dep = add_ports(dep, 1, jupiter_config.SSH_DOCKER)

    return dep
