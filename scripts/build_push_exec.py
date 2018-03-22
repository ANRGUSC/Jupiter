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
import configparser

INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)



sys.path.append(jupiter_config.EXEC_PATH)
import exec_docker_files_generator as dc

port_list_home = []
port_list_home.append(jupiter_config.SSH_DOCKER)
port_list_home.append(jupiter_config.MONGO_DOCKER)
port_list_home.append(jupiter_config.FLASK_DOCKER)
for key in config["DOCKER_PORT"]:
  print(config["DOCKER_PORT"][key])
  port_list_home.append(config["DOCKER_PORT"][key])
print('The list of ports to be exposed in the exec home dockers are ', " ".join(port_list_home))

port_list_worker = []
port_list_worker.append(jupiter_config.SSH_DOCKER)
port_list_worker.append(jupiter_config.MONGO_DOCKER)
port_list_worker.append(jupiter_config.FLASK_DOCKER)
print('The list of ports to be exposed in the exec worker dockers are ', " ".join(port_list_worker))


def build_push_exec():

    os.chdir(jupiter_config.EXEC_PATH )

    dc.write_exec_home_docker(username = jupiter_config.USERNAME,
                     password = jupiter_config.PASSWORD,
                     app_file = jupiter_config.APP_NAME,
                     ports = " ".join(port_list_home))

    dc.write_exec_worker_docker(username = jupiter_config.USERNAME,
                     password = jupiter_config.PASSWORD,
                     app_file=jupiter_config.APP_NAME,
                     ports = " ".join(port_list_worker))

    os.system("sudo docker build -f exec_home.Dockerfile .. -t "
                                 + jupiter_config.EXEC_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.EXEC_HOME_IMAGE)

    os.system("sudo docker build -f exec_worker.Dockerfile .. -t "
                                 + jupiter_config.EXEC_WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.EXEC_WORKER_IMAGE)

    # os.system("rm *.Dockerfile")

if __name__ == '__main__':
    build_push_exec()
