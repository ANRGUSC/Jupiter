__author__ = "Quynh Nguyen and  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "4.0"

import sys
sys.path.append("../")
import os
import configparser
import jupiter_config
import logging

logging.basicConfig(level = logging.DEBUG)

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
    sys.path.append(jupiter_config.SINK_PATH)
    port_list_home = []
    port_list_home.append(jupiter_config.SSH_DOCKER)
    port_list_home.append(jupiter_config.FLASK_DOCKER)
    logging.debug('The list of ports to be exposed in the sim home are %s', " ".join(port_list_home))

    return port_list_home
    
def build_push_sink():
    """Build sinker home image from Docker files and push them to the Dockerhub.
    """

    port_list_home = prepare_global_info()
    import sink_docker_files_generator as dc 

    os.chdir(jupiter_config.SINK_PATH)

    home_file = dc.write_sink_home_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = " ".join(port_list_home))

    #--no-cache
    cmd = "sudo docker build -f %s ../.. -t %s"%(home_file,jupiter_config.SINK_IMAGE)
    os.system(cmd)
    os.system("sudo docker push " + jupiter_config.SINK_IMAGE )

    # os.system("rm *.Dockerfile")
if __name__ == '__main__':
    build_push_sink()
