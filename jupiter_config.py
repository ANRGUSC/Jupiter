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
	global STATIC_MAPPING, SCHEDULER, TRANSFER, PROFILER, RUNTIME, PRICING, PRICE_OPTION

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
	# Pricing option from pricing option list
	PRICE_OPTION          = int(config['CONFIG']['PRICE_OPTION'])

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

	global mapper_option
	

	if SCHEDULER == int(config['SCHEDULER_LIST']['WAVE_RANDOM']):
	    WAVE_PATH           = HERE + 'task_mapper/wave/random_wave/'
	    mapper_option 		= 'random'
	elif SCHEDULER == int(config['SCHEDULER_LIST']['WAVE_GREEDY']):
	    WAVE_PATH           = HERE + 'task_mapper/wave/greedy_wave/'
	    mapper_option 		= 'greedy'
	elif SCHEDULER == int(config['SCHEDULER_LIST']['HEFT_MODIFIED']):
		HEFT_PATH           = HERE + 'task_mapper/heft/modified/'	
		mapper_option 		= 'modified'

	global pricing_option, profiler_option

	pricing_option 			= 'pricing' #original pricing
	profiler_option     	= 'onehome'
	mapper_option           = 'heft'

	if PRICING == 2:#separated
		pricing_option 		= 'pricing_separate'
	if PRICING == 3:#decoupled
		pricing_option 		= 'pricing_decouple'
	if PRICING == 4:#home
		pricing_option 		= 'pricing_home'
	if PRICING == 5:#multiple home
		pricing_option 		= 'pricing_multiple_home'
		profiler_option     = 'multiple_home'
		NETR_PROFILER_PATH      = HERE + 'profilers/network_resource_profiler_mulhome/'

	CIRCE_PATH          	= HERE + 'circe/%s/'%(pricing_option)
	if PRICING == 0: #non-pricing
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
	#HOME_CHILD              = 'task1'
	HOME_CHILD              = 'localpro'

	"""pricing CIRCE home and worker images"""
	global PRICING_HOME_IMAGE, WORKER_CONTROLLER_IMAGE, WORKER_COMPUTING_IMAGE

	PRICING_HOME_IMAGE 		= 'docker.io/anrg/%s_circe_home:coded' %(pricing_option)
	WORKER_CONTROLLER_IMAGE = 'docker.io/anrg/%s_circe_controller:coded' %(pricing_option)
	WORKER_COMPUTING_IMAGE  = 'docker.io/anrg/%s_circe_computing:coded' %(pricing_option)
	
	"""CIRCE home and worker images for execution profiler"""
	global HOME_IMAGE, WORKER_IMAGE

	HOME_IMAGE              = 'docker.io/anrg/circe_home:coded'
	WORKER_IMAGE            = 'docker.io/anrg/circe_worker:coded'

	"""DRUPE home and worker images"""
	global PROFILER_HOME_IMAGE, PROFILER_WORKER_IMAGE
	
	PROFILER_HOME_IMAGE     = 'docker.io/anrg/%s_profiler_home:coded'%(profiler_option)
	PROFILER_WORKER_IMAGE   = 'docker.io/anrg/%s_profiler_worker:coded'%(profiler_option)

	"""WAVE home and worker images"""
	global WAVE_HOME_IMAGE, WAVE_WORKER_IMAGE

	#coded: random, v1: greedy

	WAVE_HOME_IMAGE         = 'docker.io/anrg/%s_wave_home:coded' %(mapper_option)
	WAVE_WORKER_IMAGE       = 'docker.io/anrg/%s_wave_worker:coded' %(mapper_option)

	"""Execution profiler home and worker images"""
	global EXEC_HOME_IMAGE, EXEC_WORKER_IMAGE


	EXEC_HOME_IMAGE         = 'docker.io/anrg/exec_home:coded'
	EXEC_WORKER_IMAGE       = 'docker.io/anrg/exec_worker:coded'

	"""HEFT docker image"""
	global HEFT_IMAGE

	HEFT_IMAGE              = 'docker.io/anrg/heft:coded'

	"""Application Information"""
	global APP_PATH, APP_NAME

	APP_PATH                = HERE  + 'app_specific_files/network_monitoring_app_dag/'
	APP_NAME                = 'app_specific_files/network_monitoring_app_dag'

	# APP_PATH                = HERE  + 'app_specific_files/dummy_app/'
	# APP_NAME                = 'app_specific_files/dummy_app'

if __name__ == '__main__':
	set_globals()