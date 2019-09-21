__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import yaml
import sys
sys.path.append("../")
import jupiter_config


template = """
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
        - name: APP_NAME
          value: {app_name}
        - name: APP_OPTION
          value: {app_option}
        - name: CHILD_NODES
          value: {child}
"""

def write_wave_specs(**kwargs):
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
    
    specific_yaml = template.format(flask_port = jupiter_config.FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep

template_modified = """
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
        - name: ALL_NODES_GEO
          value: {all_node_geo}
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

def write_wave_modified_specs(**kwargs):
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
    
    specific_yaml = template_modified.format(flask_port = jupiter_config.FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep



template_worker = """
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
        - name: ALL_NODES_GEO
          value: {all_node_geo}
        - name: MY_GEO
          value: {my_geo}
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

def write_wave_worker_specs(**kwargs):
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
    
    specific_yaml = template_worker.format(flask_port = jupiter_config.FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep