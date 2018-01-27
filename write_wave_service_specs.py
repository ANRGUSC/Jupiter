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
    purpose: wave-demo
spec:
  ports:
  - port: 48080
    targetPort: 8080
  selector:
    app: {label}
"""

## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, name = {taskname}
def write_wave_service_specs(**kwargs):
    # insert your values
    specific_yaml = template.format(**kwargs)
    dep = yaml.load(specific_yaml)
    return dep
