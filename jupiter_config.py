"""
Top level config file (leave this file at the root directory). ``import config`` on the top of your file to include the global information included here.

"""
__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"


from os import path
import os
import configparser

HERE       = path.abspath(path.dirname(__file__)) + "/"
INI_PATH   = HERE + 'jupiter_config.ini'

def get_home_node(file_name):
    with open(file_name) as file:
        line = file.readline().split()
    return line[1]

def set_globals():
	"""Set global configuration information
	"""

	"""Configuration Paths"""

	config = configparser.ConfigParser()
	config.read(INI_PATH)
	"""User input for scheduler information"""
	global STATIC_MAPPING, SCHEDULER 

	STATIC_MAPPING          = int(config['CONFIG']['STATIC_MAPPING'])
	SCHEDULER               = int(config['CONFIG']['SCHEDULER'])

	"""Authorization information in the containers"""
	global USERNAME, PASSWORD

	USERNAME                = config['AUTH']['USERNAME']
	PASSWORD                = config['AUTH']['PASSWORD']

	"""Port and target port in containers for services to be used: Mongo, SSH and Flask"""
	global MONGO_SVC, MONGO_DOCKER, SSH_SVC, SSH_DOCKER, FLASK_SVC, FLASK_DOCKER
	
	MONGO_SVC               = config['PORT']['MONGO_SVC']
	MONGO_DOCKER            = config['PORT']['MONGO_DOCKER']
	SSH_SVC                 = config['PORT']['SSH_SVC']
	SSH_DOCKER              = config['PORT']['SSH_DOCKER']
	FLASK_SVC               = config['PORT']['FLASK_SVC']
	FLASK_DOCKER            = config['PORT']['FLASK_DOCKER']

	"""Modules path of Jupiter"""
	global NETR_PROFILER_PATH, EXEC_PROFILER_PATH, CIRCE_PATH, HEFT_PATH, WAVE_PATH, SCRIPT_PATH 

	NETR_PROFILER_PATH      = HERE + 'profilers/network_resource_profiler/'
	EXEC_PROFILER_PATH      = HERE + 'profilers/execution_profiler/'
	CIRCE_PATH              = HERE + 'circe/'
	HEFT_PATH               = HERE + 'task_mapper/heft/'
	WAVE_PATH               = HERE + 'task_mapper/wave/random_wave/'
	SCRIPT_PATH             = HERE + 'scripts/'

	if SCHEDULER == 1:
	    WAVE_PATH           = HERE + 'task_mapper/wave/random_wave/'
	elif SCHEDULER == 2:
	    WAVE_PATH           = HERE + 'task_mapper/wave/greedy_wave/'

	"""Kubernetes required information"""
	global KUBECONFIG_PATH, DEPLOYMENT_NAMESPACE, PROFILER_NAMESPACE, MAPPER_NAMESPACE, EXEC_NAMESPACE

	KUBECONFIG_PATH         = os.environ['KUBECONFIG']

	# Namespaces
	DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
	PROFILER_NAMESPACE      = 'johndoe-profiler'
	MAPPER_NAMESPACE        = 'johndoe-mapper'
	EXEC_NAMESPACE          = 'johndoe-exec'

	""" Node file path and first task information """
	global HOME_NODE, HOME_CHILD

	HOME_NODE               = get_home_node(HERE + 'nodes.txt')
	HOME_CHILD              = 'sample_ingress_task'

	"""CIRCE home and worker images"""
	global HOME_IMAGE, WORKER_IMAGE

	HOME_IMAGE              = 'docker.io/johndoe/circe_home:v0'
	WORKER_IMAGE            = 'docker.io/johndoe/circe_worker:v0'

	"""DRUPE home and worker images"""
	global PROFILER_HOME_IMAGE, PROFILER_WORKER_IMAGE
	
	PROFILER_HOME_IMAGE     = 'docker.io/johndoe/profiler_home:v0'
	PROFILER_WORKER_IMAGE   = 'docker.io/johndoe/profiler_worker:v0'

	"""WAVE home and worker images"""
	global WAVE_HOME_IMAGE, WAVE_WORKER_IMAGE

	#v0: random, v1: greedy

	WAVE_HOME_IMAGE         = 'docker.io/johndoe/wave_home:v0'
	WAVE_WORKER_IMAGE       = 'docker.io/johndoe/wave_worker:v0'

	"""Execution profiler home and worker images"""
	global EXEC_HOME_IMAGE, EXEC_WORKER_IMAGE


	EXEC_HOME_IMAGE         = 'docker.io/johndoe/exec_home:v0'
	EXEC_WORKER_IMAGE       = 'docker.io/johndoe/exec_worker:v0'

	"""HEFT docker image"""
	global HEFT_IMAGE

	HEFT_IMAGE              = 'docker.io/johndoe/heft:v0'

	"""Application Information"""
	global APP_PATH, APP_NAME

	APP_PATH                = HERE  + 'app_specific_files/network_monitoring_app/'
	APP_NAME                = 'app_specific_files/network_monitoring_app'

if __name__ == '__main__':
	set_globals()