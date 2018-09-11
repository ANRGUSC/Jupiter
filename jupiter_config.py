"""
Top level config file (leave this file at the root directory). ``import config`` on the top of your file to include the global information included here.
"""
__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,  Jason A Tran, Bhaskar Krishnamachari"
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
	global STATIC_MAPPING, SCHEDULER, TRANSFER, PROFILER, RUNTIME, PRICING 

	STATIC_MAPPING          = int(config['CONFIG']['STATIC_MAPPING'])
	# scheduler option chosen from SCHEDULER_LIST
	SCHEDULER               = int(config['CONFIG']['SCHEDULER'])
	# transfer option chosen from TRANSFER_LIST
	TRANSFER 				= int(config['CONFIG']['TRANSFER'])
	# Network and Resource profiler (TA2) option chosen from TA2_LIST
	PROFILER                = int(config['CONFIG']['PROFILER'])
	# Runtime profiling for data transfer methods: 0 for only senders, 1 for both senders and receivers
	RUNTIME                 = int(config['CONFIG']['RUNTIME'])
	# Using pricing or original scheme
	PRICING                 = int(config['CONFIG']['PRICING'])

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
	global NETR_PROFILER_PATH, EXEC_PROFILER_PATH, CIRCE_PATH, HEFT_PATH, WAVE_PATH, SCRIPT_PATH, CIRCE_ORIGINAL_PATH

	# default network and resource profiler: DRUPE
	# default wave mapper: random wave
	NETR_PROFILER_PATH      = HERE + 'profilers/network_resource_profiler/'
	EXEC_PROFILER_PATH      = HERE + 'profilers/execution_profiler/'
	CIRCE_PATH              = HERE + 'circe/pricing/'
	HEFT_PATH               = HERE + 'task_mapper/heft/original/'
	WAVE_PATH               = HERE + 'task_mapper/wave/random_wave/'
	SCRIPT_PATH             = HERE + 'scripts/'

	if SCHEDULER == int(config['SCHEDULER_LIST']['WAVE_RANDOM']):
	    WAVE_PATH           = HERE + 'task_mapper/wave/random_wave/'
	elif SCHEDULER == int(config['SCHEDULER_LIST']['WAVE_GREEDY']):
	    WAVE_PATH           = HERE + 'task_mapper/wave/greedy_wave/'
	elif SCHEDULER == int(config['SCHEDULER_LIST']['HEFT_MODIFIED']):
		HEFT_PATH           = HERE + 'task_mapper/heft/modified/'	

	if PRICING == 0:
		CIRCE_PATH          = HERE + 'circe/original/'	
	
	"""Kubernetes required information"""
	global KUBECONFIG_PATH, DEPLOYMENT_NAMESPACE, PROFILER_NAMESPACE, MAPPER_NAMESPACE, EXEC_NAMESPACE

	KUBECONFIG_PATH         = os.environ['KUBECONFIG']

	# Namespaces
	DEPLOYMENT_NAMESPACE    = 'quynh-circe'
	PROFILER_NAMESPACE      = 'quynh-profiler'
	MAPPER_NAMESPACE        = 'quynh-mapper'
	EXEC_NAMESPACE          = 'quynh-exec'

	""" Node file path and first task information """
	global HOME_NODE, HOME_CHILD

	HOME_NODE               = get_home_node(HERE + 'nodes.txt')
	HOME_CHILD              = 'task1'
	#HOME_CHILD              = 'localpro'

	"""pricing CIRCE home and worker images"""
	global PRICING_HOME_IMAGE, WORKER_CONTROLLER_IMAGE, WORKER_COMPUTING_IMAGE

	PRICING_HOME_IMAGE 		= 'docker.io/anrg/pricing_circe_home:mdummy'
	WORKER_CONTROLLER_IMAGE = 'docker.io/anrg/pricing_circe_controller:mdummy'
	WORKER_COMPUTING_IMAGE  = 'docker.io/anrg/pricing_circe_computing:mdummy'
	
	"""CIRCE home and worker images for execution profiler"""
	global HOME_IMAGE, WORKER_IMAGE

	HOME_IMAGE              = 'docker.io/anrg/circe_home:mdummy'
	WORKER_IMAGE            = 'docker.io/anrg/circe_worker:mdummy'

	"""DRUPE home and worker images"""
	global PROFILER_HOME_IMAGE, PROFILER_WORKER_IMAGE
	
	PROFILER_HOME_IMAGE     = 'docker.io/anrg/profiler_home:mdummy'
	PROFILER_WORKER_IMAGE   = 'docker.io/anrg/profiler_worker:mdummy'

	"""WAVE home and worker images"""
	global WAVE_HOME_IMAGE, WAVE_WORKER_IMAGE

	#mdummy: random, v1: greedy

	WAVE_HOME_IMAGE         = 'docker.io/anrg/wave_home:mdummy'
	WAVE_WORKER_IMAGE       = 'docker.io/anrg/wave_worker:mdummy'

	"""Execution profiler home and worker images"""
	global EXEC_HOME_IMAGE, EXEC_WORKER_IMAGE


	EXEC_HOME_IMAGE         = 'docker.io/anrg/exec_home:mdummy'
	EXEC_WORKER_IMAGE       = 'docker.io/anrg/exec_worker:mdummy'

	"""HEFT docker image"""
	global HEFT_IMAGE

	HEFT_IMAGE              = 'docker.io/anrg/heft:mdummy'

	"""Application Information"""
	global APP_PATH, APP_NAME, APP_ID 

	# APP_PATH                = HERE  + 'app_specific_files/network_monitoring_app_dag/'
	# APP_NAME                = 'app_specific_files/network_monitoring_app_dag'

	APP_PATH                = HERE  + 'app_specific_files/dummy_app/'
	APP_NAME                = 'app_specific_files/dummy_app'
	APP_ID					= 'dummy'

if __name__ == '__main__':
	set_globals()