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
    purpose: wave-demo
spec:
  ports:
  - port: {flask_svc}
    targetPort: {flask_port}
  selector:
    app: {label}
"""

## \brief this function genetares the service description yaml for a task 
# \param kwargs             list of key value pair. 
# In this case, call argument should be, name = {taskname}
def write_wave_service_specs(**kwargs):
    # insert your values
    specific_yaml = template.format(flask_svc = FLASK_SVC,
                                    flask_port = FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep
