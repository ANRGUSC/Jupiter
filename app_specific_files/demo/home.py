import os
import sys
import queue
import threading
import logging
import time
import string
import random


logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
    from jupiter_utils import app_config_parser
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../core/")
    from jupiter_utils import app_config_parser

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)




# Run by dispatcher (e.g. CIRCE)
def task(q, pathin, pathout, task_name):
    # task_name will be "home"
    children = app_config.child_tasks(task_name)
    log.info(f"My children are {children}")

    while True:
        time.sleep(1)
        log.info("Staying idle...")

    log.error("ERROR: should never reach this")


if __name__ == '__main__':
    # Testing Only
    q = queue.Queue()
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    t = threading.Thread(target=task, args=(q, "./", "./", "test"))
    t.start()
