__author__ = "Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"
"""
Produces load on all available CPU cores
"""
from multiprocessing import Pool
from multiprocessing import cpu_count
import psutil
import time
import os
from flask import Flask, request

app = Flask(__name__)

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        print("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)

def start_stress_test():
    try:
        print('---- Start running stress test')
        cmd = 'python3 stress_test.py &'
        os.system(cmd)
    except Exception as e:
        print("Could not start stress test")
        print(e)
        return "not ok"
    return "ok"
app.add_url_rule('/start_stress_test', 'start_stress_test', start_stress_test)

def cpu_test(t1,t2):
    while True:
        count = cpu_count()
        print('-' * 20)
        print('Checking CPU utilization')
        print('Utilizing %d cores' % count)
        print('-' * 20)
        for i in range(0,t1+t2):
            print('------- Current CPU usage '+ str(psutil.cpu_percent()))
            time.sleep(3)  

if __name__ == '__main__':
    t1 = 100
    t2 = 5
    cpu_test(t1,t2)    
    web_server = MonitorRecv()
    web_server.start()
       