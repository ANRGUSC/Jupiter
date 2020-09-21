__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import yaml
import sys
sys.path.append("../")
import jupiter_config
import configparser


template_home_controller = """
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
        - name: ALL_NODES
          value: {all_node}
        - name: ALL_NODES_IPS
          value: {all_node_ips}
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
        - name: COMPUTE_HOME_IP
          value: {compute_home_ip}
        - name: APP_OPTION
          value: {app_option}
        - name: APP_NAME
          value: {app_name}
        - name: CHILD_NODES
          value: {child}
"""

def write_decoupled_pricing_controller_home_specs(**kwargs):
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
    
    specific_yaml = template_home_controller.format(flask_port = jupiter_config.FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep

template_worker_controller = """
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
        - name: ALL_NODES
          value: {all_node}
        - name: ALL_NODES_IPS
          value: {all_node_ips}
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
        - name: CHILD_NODES
          value: {child}
"""

def write_decoupled_pricing_controller_worker_specs(**kwargs):
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
    
    specific_yaml = template_worker_controller.format(flask_port = jupiter_config.FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep


template_compute_worker = """
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

def write_decoupled_circe_compute_worker_specs(**kwargs):
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
    
    specific_yaml = template_compute_worker.format(flask_port = jupiter_config.FLASK_DOCKER,
                                              ssh_port = jupiter_config.SSH_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep

template_compute_home = """
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
          value: {name}
        - name: APPNAME
          value: {appname}
        - name: APPOPTION
          value: {appoption}
        - name: ALL_COMPUTING_NODES
          value: {all_computing_nodes}
        - name: ALL_COMPUTING_IPS
          value: {all_computing_ips}
        - name: SELF_PROFILER_IP
          value: {profiler_ip}
        - name: ALL_PROFILERS
          value: {all_profiler_ips}
        - name: ALL_PROFILERS_NODES
          value: {all_profiler_nodes}
        - name: HOME_NODE
          value: {home_node_ip}
      nodeSelector:
        kubernetes.io/hostname: {host}        
      restartPolicy: Always
"""


def write_decoupled_circe_compute_home_specs(**kwargs):
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

    specific_yaml = template_compute_home.format(ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)

    dep = yaml.load(specific_yaml)
    return dep