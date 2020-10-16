import os
import sys
import queue
import threading
import logging
import time

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
    from jupiter_utils import app_config_parser
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../mulhome_scripts/")
    from jupiter_utils import app_config_parser

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)


# Run by dispatcher (e.g. CIRCE). Custom tasks are unable to receive files
# even though a queue is setup. Custom tasks can, however, send files to any
# DAG task.
def task(q, pathin, pathout, task_name):
    log.info(f"Starting non-DAG task {task_name}")
    while True:
        time.sleep(999)

    log.error("ERROR: should never reach this")


if __name__ == '__main__':
    # Testing Only
    q = queue.Queue()
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    t = threading.Thread(target=task, args=(q, "./", "./", "test"))
    t.start()
