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

    sys.path.append(jupiter_config.EXEC_PROFILER_PATH)
    
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

    return port_list_home, port_list_worker

def build_push_exec():
    """Build execution profiler home and worker image from Docker files and push them to the Dockerhub.
    """
    port_list_home, port_list_worker = prepare_global_info()
    import exec_docker_files_generator as dc

    os.system("cp " + jupiter_config.SCRIPT_PATH + "keep_alive.py " 
                    + jupiter_config.EXEC_PROFILER_PATH + "keep_alive.py")

    os.chdir(jupiter_config.EXEC_PROFILER_PATH )

    dc.write_exec_home_docker(username = jupiter_config.USERNAME,
                     password = jupiter_config.PASSWORD,
                     app_file = jupiter_config.APP_NAME,
                     ports = " ".join(port_list_home))

    dc.write_exec_worker_docker(username = jupiter_config.USERNAME,
                     password = jupiter_config.PASSWORD,
                     app_file=jupiter_config.APP_NAME,
                     ports = " ".join(port_list_worker))

    os.system("sudo docker build -f exec_home.Dockerfile ../.. -t "
                                 + jupiter_config.EXEC_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.EXEC_HOME_IMAGE)

    os.system("sudo docker build -f exec_worker.Dockerfile ../.. -t "
                                 + jupiter_config.EXEC_WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.EXEC_WORKER_IMAGE)

    os.system("rm keep_alive.py")

if __name__ == '__main__':
    prepare_global_info()
    build_push_exec()
