"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""

import yaml
import sys
sys.path.append("../")
from jupiter_config import *


template_nondag = """
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
            imagePullPolicy: Always
            image: {image}
            ports:
            - containerPort: {ssh_port}
            - containerPort: {python_port}
            - containerPort: {mongo_port}
            - containerPort: 80
            - containerPort: {flask_port}
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
          restartPolicy: Always

"""

## \brief this function genetares the service description yaml for a task
# \param kwargs             list of key value pair.
# In this case, call argument should be,
# name = {taskname}, image = {image name}, child = {child node list}, host = {hostname}
def write_exec_specs_non_dag_tasks(**kwargs):
    # insert your values

    specific_yaml = template_nondag.format(ssh_port = SSH_DOCKER, 
                                    flask_port = FLASK_DOCKER,
                                    mongo_port = MONGO_DOCKER,
                                    python_port = PYTHON_PORT,
                                    **kwargs)

    dep = yaml.load(specific_yaml, Loader=yaml.BaseLoader)

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
            imagePullPolicy: Always
            image: {image}
            ports:
            - containerPort: {ssh_port}
            - containerPort: {python_port}
            - containerPort: {mongo_port}
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
            - name: ALL_PROFILERS_IPS
              value: {allprofiler_ips}
            - name: ALL_PROFILERS_NAMES
              value: {allprofiler_names}
          nodeSelector:
            kubernetes.io/hostname: {host}
          restartPolicy: Always

"""

## \brief this function genetares the service description yaml for a task
# \param kwargs             list of key value pair.
# In this case, call argument should be,
# name = {taskname}, image = {image name}, child = {child node list}, host = {hostname}
def write_exec_specs_home_control(**kwargs):
    # insert your values

    specific_yaml = template_home.format(ssh_port = SSH_DOCKER, 
                                    flask_port = FLASK_DOCKER,
                                    mongo_port = MONGO_DOCKER,
                                    python_port = PYTHON_PORT,
                                    **kwargs)

    dep = yaml.load(specific_yaml, Loader=yaml.BaseLoader)

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
      - name: network-profiler
        imagePullPolicy: Always
        image: {image}
        ports:
        - name: sshport
          containerPort: {ssh_port}
        - name: flaskport
          containerPort: {flask_port}
        - name: mongoport
          containerPort: {mongo_port}
        env:
        - name: HOME_NODE
          value: {home_node_ip}
        - name: NODE_NAME
          value: {node_name}
"""



## \brief this function genetares the service description yaml for a task
# \param kwargs             list of key value pair.
# In this case, call argument should be,
# name = {taskname}, dir = '{}', host = {hostname}

def write_exec_specs(**kwargs):
    specific_yaml = template_worker.format(ssh_port = SSH_DOCKER, 
                                    flask_port = FLASK_DOCKER,
                                    mongo_port = MONGO_DOCKER,
                                    python_port = PYTHON_PORT,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep
