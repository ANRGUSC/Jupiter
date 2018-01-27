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


here = path.abspath(path.dirname(__file__))

KUBECONFIG_PATH         = os.environ['KUBECONFIG']
DEPLOYMENT_NAMESPACE    = 'pranav-circe'
PROFILER_NAMESPACE      = 'pranav-profiler'
WAVE_NAMESPACE          = 'pranav-wave'

DFT_CODING_NAMESPACE    = 'pranav-dft-coding'
TERA_CODING_NAMESPACE   = 'pranav-tera-coding'

#home's child node is hardcoded in write_home_specs.py
HOME_NODE               = 'ubuntu-2gb-ams2-04' 
HOME_IMAGE              = 'docker.io/anrg/home_node:test' 
HOME_CHILD              = 'localpro'

WORKER_IMAGE            = 'docker.io/anrg/worker_node:test'

# Profiler Path
PROFILER_PATH           = 'Profilers/'
PROFILER_HOME_IMAGE     = 'anrg/central_profiler:v2'
PROFILER_WORKER_IMAGE   = 'anrg/worker_profiler:v2' 

# WAVE scheduler variables
WAVE_HOME_IMAGE         = 'anrg/wave_home:test1'
WAVE_WORKER_IMAGE       = 'anrg/wave_worker:test1'

APP_PATH                = 'task_specific_files/network_monitoring_app/'
