__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import sys
sys.path.append("../")
import os
import configparser
import jupiter_config

def prepare_global_info():
    """Read configuration information from ``app_config.ini``
    
    Returns:
        - list: port_list_home - The list of ports to be exposed in the exec home dockers
        - list: port_list_worker - The list of ports to be exposed in the exec worker dockers
    """
    
    jupiter_config.set_globals()
    INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    sys.path.append(jupiter_config.CIRCE_PATH)
    port_list_home = []
    port_list_home.append(jupiter_config.SSH_DOCKER)
    port_list_home.append(jupiter_config.FLASK_DOCKER)
    print('The list of ports to be exposed in the circe home are ', " ".join(port_list_home))


    port_list_worker = []
    port_list_worker.append(jupiter_config.SSH_DOCKER)
    for key in config["DOCKER_PORT"]:
      print(config["DOCKER_PORT"][key])
      port_list_worker.append(config["DOCKER_PORT"][key])
    print('The list of ports to be exposed in the circe workers are ', " ".join(port_list_worker))

    return port_list_home, port_list_worker
    
def build_push_circe():
    """Build CIRCE home and worker image from Docker files and push them to the Dockerhub.
    """

    port_list_home, port_list_worker = prepare_global_info()
    import circe_docker_files_generator as dc 

    os.chdir(jupiter_config.CIRCE_PATH)

    dc.write_circe_home_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = " ".join(port_list_home))

    dc.write_circe_worker_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = " ".join(port_list_worker))

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
