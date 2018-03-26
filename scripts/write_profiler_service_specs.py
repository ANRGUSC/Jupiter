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
apiVersion: v1
kind: Service
metadata:
  name: {name}
  labels:
    purpose: dag-demo
spec:
  ports:
  - name: ssh
    port: {ssh_svc}
    targetPort: {ssh_port}
  - name: internet
    port: 80
    targetPort: 80
  - name: flask
    port: {flask_svc}
    targetPort: {flask_port}
  - name: mongo
    port: {mongo_svc}
    targetPort: {mongo_port}
  selector:
    app: {label}
"""

## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, name = {taskname}
def write_profiler_service_specs(**kwargs):
    # insert your values

    specific_yaml = template.format(ssh_svc = SSH_SVC,
                                    ssh_port = SSH_DOCKER, 
                                    flask_svc = FLASK_SVC,
                                    flask_port = FLASK_DOCKER,
                                    mongo_svc = MONGO_SVC,
                                    mongo_port = MONGO_DOCKER,
                                    **kwargs)

    dep = yaml.load(specific_yaml)
    return dep
