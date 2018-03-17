"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Quynh Nguyen
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""

import yaml

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
        - containerPort: 8888
        env:
        - name: PROFILERS
          value: {profiler_ips}
        - name: NODE_NAMES
          value: {node_names}
        - name: EXECUTION_HOME_IP
          value: {execution_home_ip}
        - name: HOME_IP
          value: {home_ip}
"""

## \brief this function genetares the service description yaml for a task
# \param kwargs             list of key value pair.
# In this case, call argument should be,
# name = {taskname}, dir = '{}', host = {hostname}

def write_heft_specs(**kwargs):
    specific_yaml = template.format(**kwargs)
    dep = yaml.load(specific_yaml)
    return dep
