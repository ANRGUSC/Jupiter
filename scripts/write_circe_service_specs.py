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
import configparser

INI_PATH  = APP_PATH + 'app_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)


def add_app_specific_ports(dep):
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

## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, name = {taskname}
def write_circe_service_specs(**kwargs):
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
