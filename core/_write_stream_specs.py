__author__ = "Quynh Nguyen, Pradipta Ghosh and  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
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
      nodeSelector:
        kubernetes.io/hostname: {host}
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
          value: datasource
        - name: APPNAME
          value: {appname}
        - name: APPOPTION
          value: {appoption}
        - name: SELF_NAME
          value: {self_name}
        - name: HOME_NODE
          value: {home_node_ip}
        - name: ALL_NODES
          value: {all_nodes}
        - name: ALL_NODES_IPS
          value: {all_nodes_ips}
      restartPolicy: Always
"""

def write_stream_home_specs(**kwargs):
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
                                    **kwargs)

    dep = yaml.load(specific_yaml)
    return dep