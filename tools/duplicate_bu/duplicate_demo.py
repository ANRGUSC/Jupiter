__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "1.0"

# This script assists in duplicating demo applications on DCOMP cluster testbed
# The generated folder still needs some modifications to make it work on Jupiter

import argparse
import numpy as np
import yaml
import os
import json
import shutil
from collections import defaultdict
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)



def load_yaml(filename):
    """
    Parse yaml file into python dictionary
    :type       filename:  path to file
    :param      filename:  string
    :returns:   python dictionary of yaml contents
    :rtype:     dict
    """
    with open(filename) as f:
        app_config = yaml.load(f, Loader=yaml.FullLoader)
        # logging.debug(app_config)
    return app_config

def copy_scripts(app_path, base_path):
    try:
        # os.rename(os.path.join(app_path,'scripts'),os.path.join(app_path,'dupscripts'))
        # shutil.copytree(os.path.join(base_path,'scripts'),os.path.join(app_path,'scripts'))
        # shutil.copy(os.path.join(app_path,'dupscripts/config.json'),os.path.join(app_path,'scripts/config.json'))
        # shutil.rmtree(os.path.join(app_path,'dupscripts'))
        shutil.copytree(os.path.join(base_path,'sample_input'),os.path.join(app_path,'sample_input'))
        shutil.copytree(os.path.join(base_path,'reference'),os.path.join(app_path,'scripts/reference'))
    except Exception as e:
        logging.debug('Something wrong in copy scripts')

def gen_duplicate_scripts(app_config, app_path, base_path, base_tasks):
    copy_scripts(app_path, base_path)
    tasklist = ['home']  # 'home' always exists
    for task in app_config['application']['task_list']['worker_tasks']:
        tasklist.append(task['name'])
    for task in tasklist:
        if task in base_tasks or task == 'home':
            logging.debug('The task is a base task : ' + task)
        else:
            logging.debug('This is a new task : '+ task)
            if task.startswith('resnet'):
                # logging.debug('Resnet duplication')
                basefile = os.path.join(app_path,'scripts/resnet0.py')
                newfile = app_path+'/scripts/'+ task+'.py'
                shutil.copy(basefile,newfile)
            elif task.startswith('lccdec'):
                basefile = os.path.join(app_path,'scripts/lccdec1.py')
                newfile = app_path+'/scripts/'+ task+'.py'
                shutil.copy(basefile,newfile)
            elif task.startswith('lccenc'):
                basefile = os.path.join(app_path,'scripts/lccenc1.py')
                newfile = app_path+'/scripts/'+ task+'.py'
                shutil.copy(basefile,newfile)
            elif task.startswith('preagg'):
                basefile = os.path.join(app_path,'scripts/preagg1.py')
                newfile = app_path+'/scripts/'+ task+'.py'
                shutil.copy(basefile,newfile)
            elif task.startswith('storeclass'):
                basefile = os.path.join(app_path,'scripts/storeclass1.py')
                newfile = app_path+'/scripts/'+ task+'.py'
                shutil.copy(basefile,newfile)
            else:
                logging.debug(task)
                ch = task.split('score')[1][0]
                logging.debug(ch)
                if ch=='a':
                    basefile = os.path.join(app_path,'scripts/score1a.py')
                    newfile = app_path+'/scripts/'+ task+'.py'
                    shutil.copy(basefile,newfile)
                elif ch=='b':
                    basefile = os.path.join(app_path,'scripts/score1b.py')
                    newfile = app_path+'/scripts/'+ task+'.py'
                    shutil.copy(basefile,newfile)
                else:
                    basefile = os.path.join(app_path,'scripts/score1c.py')
                    newfile = app_path+'/scripts/'+ task+'.py'
                    shutil.copy(basefile,newfile)
    
if __name__ == '__main__':
    base_path = 'base'
    app_path = 'demo'
    app_config = load_yaml(app_path + "/app_config.yaml")
    base_tasks = ['master','collage','decoder','storeclass1','resnet0','lccenc1','lccdec1','score1a','score1b','score1c','preagg1']
    gen_duplicate_scripts(app_config, app_path, base_path, base_tasks)
    print('The application is duplicated successfully!')

