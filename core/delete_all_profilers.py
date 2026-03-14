__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")
import subprocess
import jupiter_config
from jupiter_utils import app_config_parser
import logging

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

if __name__ == '__main__':
    app_config = app_config_parser.AppConfig(jupiter_config.get_abs_app_dir())
    namespace = app_config.namespace_prefix() + "-profiler"

    subprocess.run(["kubectl", "delete", "--all", "services", f"--namespace={namespace}"], check=False)
    subprocess.run(["kubectl", "delete", "--all", "deployments", f"--namespace={namespace}"], check=False)
    log.info("Deleting namespace (will complete when all pods terminate)...")
    subprocess.run(["kubectl", "delete", "namespace", namespace], check=False)
