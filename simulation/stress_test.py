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

def stress_test(t1,t2):
    while True:
        count = cpu_count()
        print('-' * 20)
        print('Running stress test on CPU')
        print('Utilizing %d cores' % count)
        print('-' * 20)
        cmd = 'stress --cpu %d --timeout %ds &' %(count,t1)
        os.system(cmd)
        for i in range(0,t1+t2):
            print('------- Current CPU usage '+ str(psutil.cpu_percent()))
            time.sleep(1)

if __name__ == '__main__':
    t1 = 100
    t2 = 5
    stress_test(t1,t2)    
       