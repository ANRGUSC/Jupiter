__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,  Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

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
  
  a = dep['spec']['ports']

  for i in config['DOCKER_PORT']:
    dic = {}
    dic['name'] = i
    dic['port'] = int(config['SVC_PORT'][i])
    dic['targetPort'] = int(config['DOCKER_PORT'][i])
    a.append(dic)

  return dep




template_worker = """
apiVersion: v1
kind: Service
metadata:
  name: {name}
  labels:
    purpose: exec-demo
spec:
  ports:
  - name: ssh
    port: {ssh_svc}
    targetPort: {ssh_port}
  - name: internet
    port: 80
    targetPort: 80
  - port: {flask_svc}
    targetPort: {flask_port}
    name: flask-port
  - name: mongo
    port: {mongo_svc}
    targetPort: {mongo_port}
  selector:
    app: {label}
"""

def write_exec_service_specs(**kwargs):
    """
    This function genetares the service description yaml for execution profiler worker
    
    In this case, call argument should be:
    
      -   name: {name}
      -   SSH port: {ssh_svc}
      -   target SSH Port: {ssh_port}
      -   Flask port: {flask_svc}
      -   target Flask Port: {flask_port}
      -   Mongo port: {mongo_svc}
      -   target Mongo Port: {mongo_port}
      -   app: {label}
    

    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """

    jupiter_config.set_globals()

    INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    # insert your values
    specific_yaml = template_worker.format(ssh_svc = jupiter_config.SSH_SVC,
                                    ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_svc = jupiter_config.FLASK_SVC,
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_svc = jupiter_config.MONGO_SVC,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep

template_home = """
apiVersion: v1
kind: Service
metadata:
  name: {name}
  labels:
    purpose: dag-demo
spec:
  ports:
  - port: {ssh_svc}
    targetPort: {ssh_port}
    name: scp-port
  - port: {ssh_port}
    targetPort: {ssh_port}
    name: scp-port1
  - name: mongo
    port: {mongo_svc}
    targetPort: {mongo_port}
  - port: {flask_svc}
    targetPort: {flask_port}
    name: flask-port
  selector:
    app: {name}
"""


def write_exec_service_specs_home(**kwargs):
    """
    This function genetares the service description yaml for execution profiler home
    
    In this case, call argument should be:
    
      -   name: {name}
      -   SSH port: {ssh_svc}
      -   target SSH Port: {ssh_port}
      -   Flask port: {flask_svc}
      -   target Flask Port: {flask_port}
      -   Mongo port: {mongo_svc}
      -   target Mongo Port: {mongo_port}
      -   app: {name}
    

    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """

    # insert your values
    specific_yaml = template_home.format(ssh_svc = jupiter_config.SSH_SVC,
                                    ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_svc = jupiter_config.FLASK_SVC,
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_svc = jupiter_config.MONGO_SVC,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)


    dep = yaml.load(specific_yaml)
    return add_app_specific_ports(dep)
