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

import jupiter_config
import os

def build_push_profiler():

    os.chdir(jupiter_config.PROFILER_PATH + "central/")

    os.system("sudo docker build -f Dockerfile . -t "
                                 + jupiter_config.PROFILER_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.PROFILER_HOME_IMAGE)
    os.chdir("../droplet/")

    os.system("sudo docker build -f Dockerfile . -t "
                                 + jupiter_config.PROFILER_WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.PROFILER_WORKER_IMAGE)

if __name__ == '__main__':
    build_push_profiler()
