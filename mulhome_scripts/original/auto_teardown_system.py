__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")

import time
import os
from os import path
from multiprocessing import Process
from k8s_profiler_scheduler import *
from k8s_wave_scheduler import *
from k8s_pricing_circe_scheduler import *
from k8s_exec_scheduler import *
from k8s_heft_scheduler import *
from pprint import *
import jupiter_config
import requests
import json
from pprint import *
import utilities
from k8s_get_service_ips import *
from functools import wraps
from delete_all_circe import *
from delete_all_pricing_circe import *
from delete_all_integrated_pricing_circe import *
from delete_all_decoupled_pricing_circe import *
from delete_all_waves import *
from delete_all_heft import *
from delete_all_exec import *
from delete_all_profilers import *

from flask import Flask, request
import datetime

from k8s_get_service_ips import *
from functools import wraps
import _thread


def teardown_system(app_name):
    """Automatically tear down the whole system
    
    Args:
        app_name (str): Application name
    """
    jupiter_config.set_globals()
    
    static_mapping = jupiter_config.STATIC_MAPPING
    pricing = jupiter_config.PRICING
    scheduler = jupiter_config.SCHEDULER
    
    """
        Tear down all current deployments
    """
    
    if pricing == 0:
        print('Tear down all current Non-pricing CIRCE deployments')
        delete_all_circe(app_name)
    elif pricing == 3:
        delete_all_integrated_pricing_circe(app_name)
    elif pricing == 4:
        delete_all_decoupled_pricing_circe(app_name)
    else:
        print('Tear down all current Pricing CIRCE deployments')
        delete_all_pricing_circe(app_name)
    if scheduler == 0 or scheduler==3: # HEFT
        print('Tear down all current HEFT deployments')
        delete_all_heft(app_name)
    else:# WAVE
        print('Tear down all current WAVE deployments')
        delete_all_waves(app_name)



def main():
    """ 
        Deploy num_dags of the application specified by app_name
    """
    jupiter_config.set_globals()
    app_name = jupiter_config.APP_OPTION
    # delete_all_exec(app_name)
    # delete_all_profilers()

    num_dags = 1
    app_list = []
    for num in range(1,num_dags+1):
        cur_app = app_name+str(num)
        app_list.append(cur_app)     
    print(app_list)

    for app_name in app_list:
        teardown_system(app_name)   


if __name__ == '__main__':
    main()
