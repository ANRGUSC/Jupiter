__author__ = "Quynh Nguyen, Pradipta Ghosh,  Pranav Sakulkar,  Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

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
    print(jupiter_config.CIRCE_PATH)
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
    
def build_push_integrated_pricing_circe():
    """Build CIRCE home and worker image from Docker files and push them to the Dockerhub.
    """
    jupiter_config.set_globals()

    port_list_home, port_list_worker = prepare_global_info()
    import circe_docker_files_generator as dc 

    os.chdir(jupiter_config.CIRCE_PATH)

    print(jupiter_config.CIRCE_PATH)
    print(jupiter_config.USERNAME)
    print(jupiter_config.PRICING_HOME_IMAGE)
    print(jupiter_config.WORKER_CONTROLLER_IMAGE)
    print(jupiter_config.WORKER_COMPUTE_IMAGE )
    print(jupiter_config.pricing_option)

    dc.write_circe_home_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = " ".join(port_list_home),
                      pricing_option = jupiter_config.pricing_option)

    dc.write_circe_computing_worker_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = " ".join(port_list_worker),
                      pricing_option = jupiter_config.pricing_option)

    #--no-cache
    os.system("sudo docker build -f home_node.Dockerfile ../.. -t "
                             + jupiter_config.PRICING_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.PRICING_HOME_IMAGE)
  
    os.system("sudo docker build -f computing_worker_node.Dockerfile ../.. -t "
                                 + jupiter_config.WORKER_COMPUTE_IMAGE)
    os.system("sudo docker push " + jupiter_config.WORKER_COMPUTE_IMAGE)

    # only required for non-DAG tasks (Tera detectors and DFT detectors)
    print(jupiter_config.APP_OPTION)
    if jupiter_config.APP_OPTION == 'coded':

      dc.write_circe_controller_nondag(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = " ".join(port_list_worker),
                      pricing_option = jupiter_config.pricing_option)
      dc.write_circe_worker_nondag(username = jupiter_config.USERNAME,
                        password = jupiter_config.PASSWORD,
                        app_file = jupiter_config.APP_NAME,
                        ports = " ".join(port_list_worker),
                        pricing_option = jupiter_config.pricing_option)
    
      os.system("sudo docker build -f controller_nondag_node.Dockerfile ../.. -t "
                                 + jupiter_config.NONDAG_CONTROLLER_IMAGE)
      os.system("sudo docker push " + jupiter_config.NONDAG_CONTROLLER_IMAGE)

      os.system("sudo docker build -f nondag_worker.Dockerfile ../.. -t "
                                 + jupiter_config.NONDAG_WORKER_IMAGE)
      os.system("sudo docker push " + jupiter_config.NONDAG_WORKER_IMAGE)

      


    # os.system("rm *.Dockerfile")
if __name__ == '__main__':
    build_push_integrated_pricing_circe()
