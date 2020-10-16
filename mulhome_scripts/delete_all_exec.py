__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,  Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")
import os
import utilities
import jupiter_config
from jupiter_config import app_config_parser
import time
import logging

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

if __name__ == '__main__':
    app_config = app_config_parser.AppConfig(jupiter_config.get_abs_app_dir())
    namespace = app_config.namespace_prefix() + "-exec"

    os.system("kubectl delete --all services --namespace={}".format(namespace))
    os.system("kubectl delete --all deployments --namespace={}".format(namespace))
    log.info("Deleting namespace (will complete when all pods terminate)...")
    os.system(f"kubectl delete namespace {namespace}")
