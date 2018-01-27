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
  - name: ssh
    port: 5100
    targetPort: 22
  - name: internet
    port: 80
    targetPort: 80
  - name: flask
    port: 6100
    targetPort: 5000
  - name: mongo
    port: 6200
    targetPort: 27017
  selector:
    app: {label}
"""

## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, name = {taskname}
def write_profiler_service_specs(**kwargs):
    # insert your values
    specific_yaml = template.format(**kwargs)
    dep = yaml.load(specific_yaml)
    return dep
