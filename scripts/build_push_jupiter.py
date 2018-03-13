"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import sys
sys.path.append("../")

from build_push_circe import *
from build_push_profiler import *
from build_push_wave import *


if __name__ == '__main__':
	build_push_wave()
	build_push_circe()
	build_push_profiler()
