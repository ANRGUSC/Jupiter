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
        - name: HOME_IP
          value: {home_ips}
        - name: HOME_ID
          value: {home_ids}
"""


def write_profiler_specs(**kwargs):
    """
    This function genetares the description yaml for network profiler
     
    In this case, call argument should be:
    
      -   name: {name}
      -   app: {label}
      -   emptyDir: {dir}
      -   kubernetes.io/hostname: {host}
      -   image: {image}
      -   SSH Port: {ssh_port}
      -   Flask Port: {flask_port}
      -   Mongo Port: {mongo_port}
      -   ALL_NODES: {all_node}
      -   ALL_NODES_IPS: {all_node_ips}
      -   SELF_NAME: {name}
      -   SELF_IP: {serv_ip}
    
    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """
    jupiter_config.set_globals()
    
    specific_yaml = template.format(ssh_port = jupiter_config.SSH_DOCKER,
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep
