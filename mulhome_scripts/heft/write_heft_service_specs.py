__author__ = "Quynh Nguyen, Pradipta Ghosh,  Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import yaml
import sys
sys.path.append("../")
import jupiter_config

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
    jupiter_config.set_globals()
    # insert your values
    specific_yaml = template.format(flask_svc = jupiter_config.FLASK_SVC,
                                    flask_port = jupiter_config.FLASK_DOCKER,
                                    **kwargs)
    dep = yaml.load(specific_yaml)
    return dep
