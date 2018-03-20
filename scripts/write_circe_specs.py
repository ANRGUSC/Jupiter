"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import yaml
import sys
sys.path.append("../")
from jupiter_config import *


template_home = """
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: home
spec:
  template:
    metadata:
      labels:
        app: home 
    spec:
      containers:
      - name: home
        image: {image}
        imagePullPolicy: Always
        ports:
        - containerPort: {ssh_port}
        - containerPort: {flask_port}
        env:
        - name: CHILD_NODES
          value: localpro
        - name: CHILD_NODES_IPS
          value: {child_ips}
        - name: TASK
          value: home
      nodeSelector:
        kubernetes.io/hostname: {host}        
      restartPolicy: Always
"""


## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, 
# name = {taskname}, dir = '{}', host = {hostname}
def write_circe_home_specs(**kwargs):
    specific_yaml = template_home.format(ssh_port = SSH_DOCKER, 
                                    flask_port = FLASK_DOCKER,
                                    mongo_port = MONGO_DOCKER,
                                    python_port = PYTHON_PORT,
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
            ports:
            - containerPort: {ssh_port}
            - containerPort: {python_port}
            - containerPort: 80
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
              value: {name}
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

## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, 
# name = {taskname}, image = {image name}, child = {child node list}, host = {hostname}
def write_circe_deployment_specs(**kwargs):
    # insert your values

    specific_yaml = template_worker.format(ssh_port = SSH_DOCKER, 
                                    flask_port = FLASK_DOCKER,
                                    mongo_port = MONGO_DOCKER,
                                    python_port = PYTHON_PORT,
                                    **kwargs)

    dep = yaml.load(specific_yaml, Loader=yaml.BaseLoader)

    return dep
