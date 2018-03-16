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

sys.path.append(jupiter_config.EXEC_PATH)
import exec_docker_files_generator as dc

def build_push_exec():

    os.chdir(jupiter_config.EXEC_PATH )

    dc.write_exec_home_docker(username = jupiter_config.USERNAME,
                     password = jupiter_config.PASSWORD,
                     app_file=jupiter_config.APP_NAME,
                     ports = '22 27017 57021 8888')

    dc.write_exec_worker_docker(username = jupiter_config.USERNAME,
                     password = jupiter_config.PASSWORD,
                     app_file=jupiter_config.APP_NAME,
                     ports = '22 27017 57021 8888')

    os.system("sudo docker build -f home.Dockerfile .. -t "
                                 + jupiter_config.EXEC_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.EXEC_HOME_IMAGE)

    os.system("sudo docker build -f worker.Dockerfile .. -t "
                                 + jupiter_config.EXEC_WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.EXEC_WORKER_IMAGE)

    # os.system("rm *.Dockerfile")

if __name__ == '__main__':
    build_push_exec()
