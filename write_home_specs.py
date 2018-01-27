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

template = """
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
        - containerPort: 22
        - containerPort: 8888
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
def write_home_specs(**kwargs):
    specific_yaml = template.format(**kwargs)
    dep = yaml.load(specific_yaml)
    return dep
