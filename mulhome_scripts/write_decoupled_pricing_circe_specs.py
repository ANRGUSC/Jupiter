__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import yaml
import sys
sys.path.append("../")
import jupiter_config
import configparser



def add_app_specific_ports(dep):
  """Add information of specific ports for the application
  
  Args:
      dep (str): deployment service description
  
  Returns:
      str: deployment service description with added specific port information for the application
  """
  jupiter_config.set_globals()

  INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
  config = configparser.ConfigParser()
  config.read(INI_PATH)
  
  a = dep['spec']['template']['spec']['containers'][0]['ports']
  for i in config['DOCKER_PORT']:
    a.append({'containerPort': int(config['DOCKER_PORT'][i])})
  return dep

template_decoupled_computing_worker = """
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: {name}
spec:
  template:
    metadata:
      labels:
        app: {label}
    spec:
      nodeSelector:
        kubernetes.io/hostname: {host}
      containers:
      - name: {name}
        imagePullPolicy: Always
        image: {image}
        ports:
        - containerPort: {flask_port}
        - containerPort: {ssh_port}
        - containerPort: 80
        env:
        - name: ALL_COMPUTING_NODES
          value: {all_computing_nodes}
        - name: ALL_COMPUTING_IPS
          value: {all_computing_ips}
        - name: NODE_NAME
          value: {node_name}
        - name: SELF_IP
          value: {self_ip}
        - name: PROFILERS
          value: {profiler_ip}
        - name: ALL_PROFILERS
          value: {all_profiler_ips}
        - name: ALL_PROFILERS_NODES
          value: {all_profiler_nodes}
        - name: EXECUTION_HOME_IP
          value: {execution_home_ip} 
        - name: HOME_NODE
          value: {home_node_ip}
        - name: CHILD_NODES
          value: {child}

"""

def write_decoupled_circe_computing_specs(**kwargs):
    """
    This function genetares the description yaml for WAVE
     
    In this case, call argument should be:
    
      -   name: {name}
      -   app: {label}
      -   kubernetes.io/hostname: {host}
      -   image: {image}
      -   Flask Port: {flask_port}
      -   ALL_NODES: {all_node}
      -   ALL_NODES_IPS: {all_node_ips}
      -   SELF_NAME: {name}
      -   SELF_IP: {serv_ip}
      -   HOME_IP: {home_ip}
      -   HOME_NAME: {home_name}
      -   PROFILER: {profiler_ip}
    
    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """
    jupiter_config.set_globals()
    
    specific_yaml = template_decoupled_computing_worker.format(flask_port = jupiter_config.FLASK_DOCKER,
                                              ssh_port = jupiter_config.SSH_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep

template_decoupled_home = """
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: {name}
spec:
  template:
    metadata:
      labels:
        app: {label}
    spec:
      nodeSelector:
        kubernetes.io/hostname: {host}
      containers:
      - name: {name}
        imagePullPolicy: Always
        image: {image}
        ports:
        - containerPort: {flask_port}
        env:
        - name: ALL_CONTROLLER
          value: {all_controller}
        - name: ALL_CONTROLLER_IPS
          value: {all_controller_ips}
        - name: SELF_NAME
          value: {self_name}
        - name: SELF_IP
          value: {serv_ip}
        - name: HOME_IP
          value: {home_ip}
        - name: HOME_NAME
          value: {home_name}
        - name: PROFILER
          value: {profiler_ip}
        - name: ALL_PROFILERS
          value: {all_profiler_ips}
        - name: HOME_PROFILER_IP
          value: {home_profiler_ip}
"""


def write_decoupled_circe_home_specs(**kwargs):
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

    specific_yaml = template_decoupled_home.format(ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)

    dep = yaml.load(specific_yaml)
    return dep

template_decoupled_controller = """
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: {name}
spec:
  template:
    metadata:
      labels:
        app: {label}
    spec:
      nodeSelector:
        kubernetes.io/hostname: {host}
      containers:
      - name: {name}
        imagePullPolicy: Always
        image: {image}
        ports:
        - containerPort: {flask_port}
        env:
        - name: ALL_CONTROLLER
          value: {all_controller}
        - name: ALL_CONTROLLER_IPS
          value: {all_controller_ips}
        - name: SELF_NAME
          value: {self_name}
        - name: SELF_IP
          value: {serv_ip}
        - name: HOME_IP
          value: {home_ip}
        - name: HOME_NAME
          value: {home_name}
        - name: PROFILER
          value: {profiler_ip}
        - name: ALL_PROFILERS
          value: {all_profiler_ips}
        - name: HOME_PROFILER_IP
          value: {home_profiler_ip}
"""

def write_decoupled_circe_controller_specs(**kwargs):
    """
    This function genetares the description yaml for WAVE
     
    In this case, call argument should be:
    
      -   name: {name}
      -   app: {label}
      -   kubernetes.io/hostname: {host}
      -   image: {image}
      -   Flask Port: {flask_port}
      -   ALL_NODES: {all_node}
      -   ALL_NODES_IPS: {all_node_ips}
      -   SELF_NAME: {name}
      -   SELF_IP: {serv_ip}
      -   HOME_IP: {home_ip}
      -   HOME_NAME: {home_name}
      -   PROFILER: {profiler_ip}
    
    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """
    jupiter_config.set_globals()
    
    specific_yaml = template_decoupled_controller.format(flask_port = jupiter_config.FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep