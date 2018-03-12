"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""

import yaml

template = """
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
            - containerPort: 22
            - containerPort: 57021
            - containerPort: 27017
            - containerPort: 80
            - containerPort: 8888
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

    specific_yaml = template.format(**kwargs)

    dep = yaml.load(specific_yaml, Loader=yaml.BaseLoader)

    return dep

template2 = """
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
            - containerPort: 22
            - containerPort: 57021
            - containerPort: 27017
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

    specific_yaml = template2.format(**kwargs)

    dep = yaml.load(specific_yaml, Loader=yaml.BaseLoader)

    return dep




template3 = """
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
          containerPort: 22
        - name: flaskport
          containerPort: 8888
        - name: mongoport
          containerPort: 27017
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
    specific_yaml = template3.format(**kwargs)
    dep = yaml.load(specific_yaml)
    return dep
