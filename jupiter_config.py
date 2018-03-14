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

if __name__ == '__main__':

	HERE                    = path.abspath(path.dirname(__file__)) + "/"
	PROFILER_PATH           = HERE + 'profilers/'
	CIRCE_PATH              = HERE + 'circe/'
	WAVE_PATH               = HERE + 'wave/'

	KUBECONFIG_PATH         = os.environ['KUBECONFIG']

	# Namespaces
	DEPLOYMENT_NAMESPACE    = 'quynh-circe'
	PROFILER_NAMESPACE      = 'quynh-profiler'
	WAVE_NAMESPACE          = 'quynh-wave'

	#home's child node is hardcoded in write_home_specs.py
	HOME_NODE               = 'ubuntu-2gb-ams2-04' 

	HOME_IMAGE              = 'docker.io/anrg/home_node:q3' 

	HOME_CHILD              = 'localpro'

	WORKER_IMAGE            = 'docker.io/anrg/worker_node:q3'

	# Profiler Path
	PROFILER_HOME_IMAGE     = 'docker.io/anrg/central_profiler:q3'
	PROFILER_WORKER_IMAGE   = 'docker.io/anrg/worker_profiler:q3' 

	# WAVE scheduler variables
	WAVE_HOME_IMAGE         = 'docker.io/anrg/wave_home:q3'
	WAVE_WORKER_IMAGE       = 'docker.io/anrg/wave_worker:q3'

	APP_PATH                = HERE  + 'task_specific_files/network_monitoring_app/'
