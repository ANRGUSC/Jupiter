"""
Top level config file (leave this file at the root directory). ``import config`` on the top of your file to include the global information included here.

"""
__author__ = "Pradipta Ghosh, Pranav Sakulkar, Jason A Tran, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"


from os import path
import os
import configparser

def get_home_node(file_name):
    with open(file_name) as file:
        line = file.readline().split()
    return line[1]


HERE                    = path.abspath(path.dirname(__file__)) + "/"
INI_PATH                = HERE + 'jupiter_config.ini'

config = configparser.ConfigParser()
config.read(INI_PATH)

STATIC_MAPPING          = int(config['CONFIG']['STATIC_MAPPING'])
SCHEDULER               = int(config['CONFIG']['SCHEDULER'])

USERNAME                = config['AUTH']['USERNAME']
PASSWORD                = config['AUTH']['PASSWORD']

MONGO_SVC               = config['PORT']['MONGO_SVC']
MONGO_DOCKER            = config['PORT']['MONGO_DOCKER']
SSH_SVC                 = config['PORT']['SSH_SVC']
SSH_DOCKER              = config['PORT']['SSH_DOCKER']
FLASK_SVC               = config['PORT']['FLASK_SVC']
FLASK_DOCKER            = config['PORT']['FLASK_DOCKER']

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

KUBECONFIG_PATH         = os.environ['KUBECONFIG']

# Namespaces

DEPLOYMENT_NAMESPACE    = 'quynh-circe'
PROFILER_NAMESPACE      = 'quynh-profiler'
MAPPER_NAMESPACE        = 'quynh-mapper'
EXEC_NAMESPACE          = 'quynh-exec'


HOME_NODE               = get_home_node(HERE + 'nodes.txt')

HOME_IMAGE              = 'docker.io/anrg/circe_home:q0'

HOME_CHILD              = 'localhost'

WORKER_IMAGE            = 'docker.io/anrg/circe_worker:q0'

# Profiler docker image
PROFILER_HOME_IMAGE     = 'docker.io/anrg/profiler_home:q0'
PROFILER_WORKER_IMAGE   = 'docker.io/anrg/profiler_worker:q0'

# WAVE docker image
WAVE_HOME_IMAGE         = 'docker.io/anrg/wave_home:q0'
WAVE_WORKER_IMAGE       = 'docker.io/anrg/wave_worker:q0'

# Execution profiler  docker image
EXEC_HOME_IMAGE         = 'docker.io/anrg/exec_home:q0'
EXEC_WORKER_IMAGE       = 'docker.io/anrg/exec_worker:q1'

# Heft docker image
HEFT_IMAGE              = 'docker.io/anrg/heft:q0'

# Application folder 
APP_PATH                = HERE  + 'app_specific_files/network_monitoring_app/'
APP_NAME                = 'app_specific_files/network_monitoring_app'
