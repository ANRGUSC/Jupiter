import logging
import os
import time
import json

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def show_run_stats(taskname,event,filename):
    runtime_stat = {
                "task_name" : taskname,
                "event" : event,
                "filename" : filename,
                "unix_time" : time.time()
    }
    log.info(f"runtime_stat:{json.dumps(runtime_stat)}")