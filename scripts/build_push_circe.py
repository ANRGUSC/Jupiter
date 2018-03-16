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

sys.path.append(jupiter_config.CIRCE_PATH)
import circe_docker_files_generator as dc 


def build_push_circe():
    os.chdir(jupiter_config.CIRCE_PATH)

    dc.write_circe_home_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = '22 8888')

    dc.write_circe_worker_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = '22 57021')

    #--no-cache
    os.system("sudo docker build -f home_node.Dockerfile .. -t "
                             + jupiter_config.HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.HOME_IMAGE)
    os.system("sudo docker build -f worker_node.Dockerfile .. -t "
                                 + jupiter_config.WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.WORKER_IMAGE)

    # os.system("rm *.Dockerfile")
if __name__ == '__main__':
    build_push_circe()
