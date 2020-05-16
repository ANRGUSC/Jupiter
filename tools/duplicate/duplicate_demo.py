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

def prepare_new_dag(demo_original_path,demo_app_path,num_branch,base_tasks,dyn_tasks):
	old_dag = os.path.join(demo_original_path,'configuration.txt')
	new_dag = os.path.join(demo_app_path,'configuration.txt')
	num_new_tasks = len(base_tasks)+len(dyn_tasks)*num_branch
	

if __name__ == '__main__':
	demo_original_path = 'demo'
	demo_app_path = 'newdemo'
	demo_config_path = demo_app_path + 'configuration.txt'
	demo_script_path = demo_app_path + 'scripts/'
	demo_json_path = demo_script_path + 'config.json' 
	demo_sample_path = demo_app_path + 'sample_input/'
	demo_name_path = demo_app_path + "name_convert.txt"

	if os.path.isdir(demo_app_path):
		shutil.rmtree(demo_app_path)
	os.mkdir(demo_app_path)

	print('Generate new DAG')	
	base_tasks = ['master','resnet0','resnet1','resnet3','resnet4','resnet5','resnet6','resnet7','resnet8','collage','decoder','home']
	dyn_tasks = ['storeclass1','lccenc1','score1a','score1b','score1c','preagg1','lccdec1']
	num_branch = 3
	prepare_new_dag(demo_original_path,demo_app_path,num_branch,base_tasks,dyn_tasks)

	# print('Generate configuration.txt')
	# generate_config(dag,demo_config_path)

	# os.mkdir(demo_script_path)

	# print('Generate application scripts')
	# generate_scripts(dag,demo_config_path,demo_script_path,demo_app_path,demo_sample_path)

	# print('Generate config.json file')
	# generate_json(dag,demo_json_path)

	# print('Generate name_convert.txt')
	# generate_nameconvert(dag,demo_name_path)
	print('The application is duplicated successfully!')