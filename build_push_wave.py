"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import os
import jupiter_config


def build_push_wave():

    os.system("cp " + jupiter_config.APP_PATH + 
                                "DAG_Scheduler.txt ./wave/home/DAG.txt")

    os.system("sudo docker build -f wave/home/Dockerfile wave/home/. -t "
                                 + jupiter_config.WAVE_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.WAVE_HOME_IMAGE)
    os.system("sudo docker build -f wave/worker/Dockerfile wave/worker/. -t "
                                 + jupiter_config.WAVE_WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.WAVE_WORKER_IMAGE)

    os.system("rm ./wave/home/DAG.txt")

if __name__ == '__main__':
    build_push_wave()