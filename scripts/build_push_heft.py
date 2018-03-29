__author__ = "Pradipta Ghosh, Pranav Sakulkar, Jason A Tran, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import sys
sys.path.append("../")

import os


def prepare_global_info():
    """Read configuration information
    """

    import jupiter_config
    
    sys.path.append(jupiter_config.HEFT_PATH)
    import heft_dockerfile_generator as dc
    port_list = []
    port_list.append(jupiter_config.SSH_DOCKER)
    port_list.append(jupiter_config.FLASK_DOCKER)
    print('The list of ports to be exposed in the heft dockers are ', " ".join(port_list))

def build_push_heft():
    """Build HEFT home and worker image from Docker files and push them to the Dockerhub.
    """
    os.system("cp " + jupiter_config.SCRIPT_PATH + "keep_alive.py " 
                    + jupiter_config.HEFT_PATH + "keep_alive.py")
    
    os.chdir(jupiter_config.HEFT_PATH)

    dc.write_heft_docker(username = jupiter_config.USERNAME,
                         password = jupiter_config.PASSWORD,
                         app_file = jupiter_config.APP_NAME,
                         ports = " ".join(port_list))

    os.system("sudo docker build -f heft.Dockerfile ../.. -t "
                                 + jupiter_config.HEFT_IMAGE)
    os.system("sudo docker push " + jupiter_config.HEFT_IMAGE)

    os.system("rm keep_alive.py")
    # os.system("rm Dockerfile")


if __name__ == '__main__':
    prepare_global_info()
    build_push_heft()