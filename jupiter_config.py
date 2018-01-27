"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""
# Top level config file (leave this file at the root directory). `import config`
# on the top of your file to include the global information included here.

from os import path
import os


HERE                    = path.abspath(path.dirname(__file__)) + "/"
PROFILER_PATH           = HERE + 'profilers/'
CIRCE_PATH              = HERE + 'circe/'
WAVE_PATH               = HERE + 'wave/'

KUBECONFIG_PATH         = os.environ['KUBECONFIG']

# Namespaces
DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
PROFILER_NAMESPACE      = 'johndoe-profiler'
WAVE_NAMESPACE          = 'johndoe-wave'

#home's child node is hardcoded in write_home_specs.py
HOME_NODE               = 'ubuntu-2gb-ams2-04' 

HOME_IMAGE              = 'docker.io/johndoe/home_node:v1' 

HOME_CHILD              = 'sample_ingress_task1'

WORKER_IMAGE            = 'docker.io/johndoe/worker_node:v1'

# Profiler Path
PROFILER_HOME_IMAGE     = 'docker.io/johndoe/central_profiler:v1'
PROFILER_WORKER_IMAGE   = 'docker.io/johndoe/worker_profiler:v1' 

# WAVE scheduler variables
WAVE_HOME_IMAGE         = 'docker.io/johndoe/wave_home:v1'
WAVE_WORKER_IMAGE       = 'docker.io/johndoe/wave_worker:v1'

APP_PATH                = HERE  + 'task_specific_files/network_monitoring_app/'
