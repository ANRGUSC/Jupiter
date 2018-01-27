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

import os
import jupiter_config

def build_push_wave():


    os.system("cp " + jupiter_config.APP_PATH + "configuration.txt " 
                    + jupiter_config.WAVE_PATH + "home/DAG.txt")

    os.system("cp " + jupiter_config.APP_PATH + "input_node.txt " 
                    + jupiter_config.WAVE_PATH + "home/input_node.txt")

    os.chdir(jupiter_config.WAVE_PATH)

    os.system("sudo docker build -f home/Dockerfile home/. -t "
                                 + jupiter_config.WAVE_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.WAVE_HOME_IMAGE)
    os.system("sudo docker build -f worker/Dockerfile worker/. -t "
                                 + jupiter_config.WAVE_WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.WAVE_WORKER_IMAGE)

    os.system("rm home/DAG.txt")
    os.system("rm home/input_node.txt")


if __name__ == '__main__':
    build_push_wave()