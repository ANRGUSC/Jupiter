__author__ = "Pradipta Ghosh, Pranav Sakulkar, Jason A Tran, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

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

def write_wave_service_specs(**kwargs):
    """
    This function genetares the service description yaml for WAVE
    
    In this case, call argument should be:
    
      -   name: {name}
      -   Flask port: {flask_svc}
      -   target Flask Port: {flask_port}
      -   app: {label}
    

    Args:
        ``**kwargs``: list of key value pair
    
    Returns:
        dict: loaded configuration 
    """

    # insert your values
    specific_yaml = template.format(flask_svc = FLASK_SVC,
                                    flask_port = FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep
