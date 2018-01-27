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

def build_push_circe():
    os.chdir(jupiter_config.CIRCE_PATH)

    #--no-cache
    os.system("sudo docker build -f home_node.Dockerfile .. -t "
                             + jupiter_config.HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.HOME_IMAGE)
    os.system("sudo docker build -f worker_node.Dockerfile .. -t "
                                 + jupiter_config.WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.WORKER_IMAGE)


if __name__ == '__main__':
    build_push_circe()
