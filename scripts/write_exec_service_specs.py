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

## \brief this function genetares the service description yaml for a task
# \param kwargs             list of key value pair.
# In this case, call argument should be, name = {taskname}
def write_exec_service_specs(**kwargs):
    # insert your values
    specific_yaml = template_worker.format(ssh_svc = SSH_SVC,
                                    ssh_port = SSH_DOCKER, 
                                    flask_svc = FLASK_SVC,
                                    flask_port = FLASK_DOCKER,
                                    mongo_svc = MONGO_SVC,
                                    mongo_port = MONGO_DOCKER,
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
  - port: {python_port}
    targetPort: {python_port}
    name: python-port
  - name: mongo
    port: {mongo_svc}
    targetPort: {mongo_port}
  - port: {flask_svc}
    targetPort: {flask_port}
    name: flask-port
  selector:
    app: {name}
"""

## \brief this function genetares the service description yaml for a task
# \param kwargs             list of key value pair.
# In this case, call argument should be, name = {taskname}
def write_exec_service_specs_home(**kwargs):
    # insert your values
    specific_yaml = template_home.format(ssh_svc = SSH_SVC,
                                    ssh_port = SSH_DOCKER, 
                                    flask_svc = FLASK_SVC,
                                    flask_port = FLASK_DOCKER,
                                    mongo_svc = MONGO_SVC,
                                    mongo_port = MONGO_DOCKER,
                                    python_port = PYTHON_PORT,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep
