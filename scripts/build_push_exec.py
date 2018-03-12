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

def build_push_exec():

    os.chdir(jupiter_config.EXEC_PATH )
    os.system("cp " + jupiter_config.APP_PATH + "configuration.txt " 
                    + jupiter_config.EXEC_PATH + "DAG.txt")


    os.system("sudo docker build -f home.Dockerfile .. -t "
                                 + jupiter_config.EXEC_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.EXEC_HOME_IMAGE)

    os.system("sudo docker build -f worker.Dockerfile .. -t "
                                 + jupiter_config.EXEC_WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.EXEC_WORKER_IMAGE)

    os.system("rm DAG.txt")

if __name__ == '__main__':
    build_push_exec()
