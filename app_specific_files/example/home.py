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
    sys.path.append("../../mulhome_scripts/")
    from jupiter_utils import app_config_parser

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)


def random_string():
    letters = string.ascii_letters + string.digits
    s = [random.choice(letters) for i in range(6)]
    return ''.join(s)


def fake_input_generator(task_name, pathout):
    children = app_config.child_tasks(task_name)

    for i in range(5):
        for child in children:
            fname = f"{task_name}_{child}_fake-{random_string()}"
            fname = os.path.join(pathout, fname)
            with open(fname, "w") as f:
                f.write("This is a fake input file of 43 characters.")

            log.info(f"created {fname}")

        time.sleep(5)


# Run by dispatcher (e.g. CIRCE)
def task(q, pathin, pathout, task_name):
    # task_name will be "home"
    # children = app_config.child_tasks(task_name)

    """
    You can generate files here to be sent to any of the child tasks. Simply
    name the files correctly (e.g. "src_dst_basefilename") and place them into
    `pathout` directory. CIRCE will transfer the files to the child tasks for
    you. fake_input_generator() is an example.
    """
    t = threading.Thread(target=fake_input_generator, args=(task_name, pathout))
    t.start()

    # If you expect the home node to receive something, read from the input
    # queue
    while True:
        input_file = q.get()

        log.info(f"Received file {input_file}")
        q.task_done()

    log.error("ERROR: should never reach this")


if __name__ == '__main__':
    # Testing Only
    q = queue.Queue()
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    t = threading.Thread(target=task, args=(q, "./", "./", "test"))
    t.start()
