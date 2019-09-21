__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")

import os
import jupiter_config


def prepare_global_info():
    """Read configuration information
    
    Returns:
        list: port_list - The list of ports to be exposed in the heft dockers
    
    """
    jupiter_config.set_globals()
      
    sys.path.append(jupiter_config.SIM_PATH)
    
    port_list = []
    port_list.append(jupiter_config.SSH_DOCKER)
    port_list.append(jupiter_config.FLASK_DOCKER)
    print('The list of ports to be exposed in the simulation dockers are ', " ".join(port_list))

    return port_list

def build_push_sim():
    """Build HEFT home and worker image from Docker files and push them to the Dockerhub.
    """

    port_list = prepare_global_info()
    os.chdir(jupiter_config.SIM_PATH)
    import sim_dockerfile_generator as dc

    dc.write_sim_docker(username = jupiter_config.USERNAME,
                         password = jupiter_config.PASSWORD,
                         ports = " ".join(port_list))

    os.system("sudo docker build -f sim.Dockerfile ../ -t "
                                 + jupiter_config.SIM_IMAGE)
    os.system("sudo docker push " + jupiter_config.SIM_IMAGE)


if __name__ == '__main__':
    build_push_sim()