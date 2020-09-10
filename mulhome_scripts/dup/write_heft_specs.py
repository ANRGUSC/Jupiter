__author__ = "Quynh Nguyen, Pradipta Ghosh,  Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
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
      - name: heft-scheduler
        imagePullPolicy: Always
        image: {image}
        ports:
        - containerPort: {flask_port}
        env:
        - name: PROFILERS
          value: {profiler_ips}
        - name: NODE_NAMES
          value: {node_names}
        - name: EXECUTION_HOME_IP
          value: {execution_home_ip}
        - name: HOME_IP
          value: {home_ip}
        - name: HOME_PROFILER_IP
          value: {home_profiler_ip}
        - name: APP_NAME
          value: {app_name}
        - name: APP_OPTION
          value: {app_option}
"""

def write_heft_specs(**kwargs):
    """
    This function genetares the deployment service description yaml for HEFT
    In this case, call argument should be:
    
      -   app: {name}
      -   kubernetes.io/hostname: {host}
      -   image: {image}
      -   app: {label}
      -   flask Port: {flask_port}
      -   PROFILERS: {profiler_ips}
      -   NODE_NAMES: {node_names}
      -   EXECUTION_HOME_IP: {execution_home_ip}
      -   HOME_IP: {home_ip}
    
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
