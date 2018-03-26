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
      volumes:
        - name: data
          emptyDir: {dir}
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
        - name: ALL_NODES
          value: {all_node}
        - name: ALL_NODES_IPS
          value: {all_node_ips}
        - name: SELF_NAME
          value: {name}
        - name: SELF_IP
          value: {serv_ip}
"""



## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, 
# name = {taskname}, dir = '{}', host = {hostname}

def write_profiler_specs(**kwargs):
    specific_yaml = template.format(ssh_port = SSH_DOCKER,
                                    flask_port = FLASK_DOCKER,
                                    mongo_port = MONGO_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep
