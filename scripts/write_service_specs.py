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
apiVersion: v1
kind: Service
metadata:
  name: {name}
  labels:
    purpose: dag-demo
spec:
  ports:
  - port: 5000
    targetPort: 22
    name: scp-port
  - port: 22
    targetPort: 22
    name: scp-port1 
  - port: 57021
    targetPort: 57021
    name: python-port
  - port: 6100
    targetPort: 8888
    name: flask-port 
  selector:
    app: {name}
"""

## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, name = {taskname}
def write_service_specs(**kwargs):
    # insert your values
    specific_yaml = template.format(**kwargs)
    dep = yaml.load(specific_yaml)
    return dep
