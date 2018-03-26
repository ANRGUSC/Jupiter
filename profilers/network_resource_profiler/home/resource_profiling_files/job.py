'''
 * Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 *     contributor: Pradipta Ghosh, Jiatong Wang, Bhaskar Krishnamachari
 *     Read license file in main directory for more details
'''

import time, os

def re_exe(cmd, inc = 60):
    while True:
        os.system(cmd)
        time.sleep(inc)

re_exe("python3 /resource_profiling/insert_to_container.py /resource_profiling/ip_path", 60)
