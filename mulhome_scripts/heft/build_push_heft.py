__author__ = "Quynh Nguyen, Pradipta Ghosh, Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
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
      
    sys.path.append(jupiter_config.HEFT_PATH)
    
    port_list = []
    port_list.append(jupiter_config.SSH_DOCKER)
    port_list.append(jupiter_config.FLASK_DOCKER)
    print('The list of ports to be exposed in the heft dockers are ', " ".join(port_list))

    return port_list

def build_push_heft():
    """Build HEFT home and worker image from Docker files and push them to the Dockerhub.
    """

    port_list = prepare_global_info()

    import heft_dockerfile_generator as dc

    
    os.chdir(jupiter_config.HEFT_PATH)

    dc.write_heft_docker(username = jupiter_config.USERNAME,
                         password = jupiter_config.PASSWORD,
                         app_file = jupiter_config.APP_NAME,
                         ports = " ".join(port_list))

    os.system("sudo docker build -f heft.Dockerfile ../../../ -t "
                                 + jupiter_config.HEFT_IMAGE)
    os.system("sudo docker push " + jupiter_config.HEFT_IMAGE)


if __name__ == '__main__':
    build_push_heft()