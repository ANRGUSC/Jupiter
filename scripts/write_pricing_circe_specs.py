__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import yaml
import sys
sys.path.append("../")
import jupiter_config
import configparser



def add_app_specific_ports(dep):
  """Add information of specific ports for the application
  
  Args:
      dep (str): deployment service description
  
  Returns:
      str: deployment service description with added specific port information for the application
  """
  jupiter_config.set_globals()

  INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
  config = configparser.ConfigParser()
  config.read(INI_PATH)
  
  a = dep['spec']['template']['spec']['containers'][0]['ports']
  for i in config['DOCKER_PORT']:
    a.append({'containerPort': int(config['DOCKER_PORT'][i])})
  return dep

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
          value: {child}
        - name: CHILD_NODES_IPS
          value: {child_ips}
        - name: TASK
          value: home
      nodeSelector:
        kubernetes.io/hostname: {host}        
      restartPolicy: Always
"""


def write_circe_home_specs(**kwargs):
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

    specific_yaml = template_home.format(ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
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
            - containerPort: 80
            - containerPort: {flask_port}
            env:
            - name: FLAG
              value: '{flag}'
            - name: INPUTNUM
              value: '{inputnum}'
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

def write_circe_deployment_specs(**kwargs):
    """
    This function genetares the deployment service description yaml for CIRCE
     
    In this case, call argument should be:
    
      -   app: {name}
      -   image: {image}
      -   containerPort: {ssh_port}
      -   FLAG: {flag}
      -   INPUTNUM: {inputnum}
      -   CHILD_NODES: {child}
      -   CHILD_NODES_IPS: {child_ips}
      -   NODE_NAME: {node_name}
      -   HOME_NODE: {home_node_ip}
      -   OWN_IP: {own_ip}
      -   ALL_NODES: {all_node}
      -   ALL_NODES_IPS: {all_node_ips}
      -   kubernetes.io/hostname: {host}
    
    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """

    # insert your values

    specific_yaml = template_worker.format(ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)

    dep = yaml.load(specific_yaml)
    #dep = yaml.load(specific_yaml, Loader=yaml.BaseLoader)
    
    dep = add_app_specific_ports(dep)



    return dep


template_computing = """
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
      - name: wave-scheduler
        imagePullPolicy: Always
        image: {image}
        ports:
        - containerPort: {flask_port}
        - containerPort: {ssh_port}
        - containerPort: 80
        env:
        - name: ALL_NODES
          value: {all_node}
        - name: ALL_NODES_IPS
          value: {all_node_ips}
        - name: ALL_COMPUTING_NODES
          value: {all_computing_nodes}
        - name: ALL_COMPUTING_IPS
          value: {all_computing_ips}
        - name: NODE_NAME
          value: {name}
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
"""

def write_circe_computing_specs(**kwargs):
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
    
    specific_yaml = template_computing.format(flask_port = jupiter_config.FLASK_DOCKER,
                                              ssh_port = jupiter_config.SSH_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep

template_controller = """
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
            - containerPort: 80
            - containerPort: {flask_port}
            env:
            - name: FLAG
              value: '{flag}'
            - name: INPUTNUM
              value: '{inputnum}'
            - name: CHILD_NODES
              value: {child}
            - name: CHILD_NODES_IPS
              value: {child_ips}
            - name: TASK
              value: {name}
            - name: NODE_NAME
              value: {node_name}
            - name: NODE_ID
              value: {node_id}
            - name: HOME_NODE
              value: {home_node_ip}
            - name: OWN_IP
              value: {own_ip}
            - name: ALL_NODES
              value: {all_node}
            - name: ALL_NODES_IPS
              value: {all_node_ips}
            - name: ALL_COMPUTING_NODES
              value: {all_computing_nodes}
            - name: ALL_COMPUTING_IPS
              value: {all_computing_ips}
          nodeSelector:
            kubernetes.io/hostname: {host}
          restartPolicy: Always

"""

def write_circe_controller_specs(**kwargs):
    """
    This function genetares the deployment service description yaml for CIRCE
     
    In this case, call argument should be:
    
      -   app: {name}
      -   image: {image}
      -   containerPort: {ssh_port}
      -   FLAG: {flag}
      -   INPUTNUM: {inputnum}
      -   CHILD_NODES: {child}
      -   CHILD_NODES_IPS: {child_ips}
      -   NODE_NAME: {node_name}
      -   HOME_NODE: {home_node_ip}
      -   OWN_IP: {own_ip}
      -   ALL_NODES: {all_node}
      -   ALL_NODES_IPS: {all_node_ips}
      -   kubernetes.io/hostname: {host}
    
    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """

    # insert your values

    specific_yaml = template_controller.format(ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)

    dep = yaml.load(specific_yaml)
    #dep = yaml.load(specific_yaml, Loader=yaml.BaseLoader)
    
    dep = add_app_specific_ports(dep)



    return dep
