__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
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
    purpose: heft-demo
spec:
  ports:
  - port: {flask_svc}
    targetPort: {flask_port}
  selector:
    app: {label}
"""


def write_heft_service_specs(**kwargs):
    """
    This function genetares the deployment service description yaml for HEFT
    
    In this case, call argument should be:
    
      -   app: {name}
      -   Flask Port: {flask_svc}
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
