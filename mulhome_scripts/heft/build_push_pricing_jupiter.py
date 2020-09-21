"""
	Build all Jupiter components (WAVE, CIRCE, DRUPE) from Docker files and push them to the Dockerhub.
"""
__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")

from build_push_circe import *
from build_push_pricing_circe import *
from build_push_profiler import *
from build_push_wave import *
from build_push_exec import *
from build_push_heft import *

if __name__ == '__main__':
	build_push_wave()
	#build_push_circe()
	build_push_pricing_circe()
	# build_push_profiler()
	# build_push_exec()
	build_push_heft()

