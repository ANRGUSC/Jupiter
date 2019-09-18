__author__ = "Quynh Nguyen and  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import yaml
import sys
sys.path.append("../")
import jupiter_config
import configparser




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

def write_sim_service_specs(**kwargs):
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
    jupiter_config.set_globals()
    
    INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)


    # insert your values
    specific_yaml = template.format(ssh_svc = jupiter_config.SSH_SVC,
                                    ssh_port = jupiter_config.SSH_DOCKER, 
                                    flask_svc = jupiter_config.FLASK_SVC,
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    mongo_svc = jupiter_config.MONGO_SVC,
                                    mongo_port = jupiter_config.MONGO_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)

    return dep
