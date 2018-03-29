__author__ = "Pradipta Ghosh, Pranav Sakulkar, Jason A Tran, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import yaml
import sys
sys.path.append("../")
from jupiter_config import *
import configparser




def add_app_specific_ports(dep):
  """Add information of specific ports for the application
  
  Args:
      dep (str): deployment service description
  
  Returns:
      str: deployment service description with added specific port information for the application
  """
  a = dep['spec']['ports']

  for i in config['DOCKER_PORT']:
    dic = {}
    dic['name'] = i
    dic['port'] = int(config['SVC_PORT'][i])
    dic['targetPort'] = int(config['DOCKER_PORT'][i])
    a.append(dic)

  return dep



template = """
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
  - port: {flask_svc}
    targetPort: {flask_port}
    name: flask-port 
  selector:
    app: {name}
"""

def write_circe_service_specs(**kwargs):
    """
    This function genetares the service description yaml for CIRCE
    
    In this case, call argument should be:
    
      -   name: {name}
      -   SSH port: {ssh_svc}
      -   target SSH Port: {ssh_port}
      -   Flask port: {flask_svc}
      -   target Flask Port: {flask_port}
      -   app: {name}
    

    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """

    INI_PATH  = APP_PATH + 'app_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    # insert your values
    specific_yaml = template.format(ssh_svc = SSH_SVC,
                                    ssh_port = SSH_DOCKER, 
                                    flask_svc = FLASK_SVC,
                                    flask_port = FLASK_DOCKER,
                                    mongo_svc = MONGO_SVC,
                                    mongo_port = MONGO_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)

    return add_app_specific_ports(dep)
