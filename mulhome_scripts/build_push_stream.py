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
from app_config_parser import *

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
    sys.path.append(jupiter_config.STREAM_PATH)
    sys.path.append(jupiter_config.STREAMS_PATH)
    port_list_home = []
    port_list_home.append(jupiter_config.SSH_DOCKER)
    port_list_home.append(jupiter_config.FLASK_DOCKER)
    logging.debug('The list of ports to be exposed in the sim home are %s', " ".join(port_list_home))

    return port_list_home
    
def build_push_stream():
    """Build STREAMer home image from Docker files and push them to the Dockerhub.
    """

    port_list_home = prepare_global_info()
    import stream_docker_files_generator as dc 

    os.chdir(jupiter_config.STREAM_PATH)

    home_file = dc.write_stream_home_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = " ".join(port_list_home))

    #--no-cache
    cmd = "sudo docker build -f %s ../.. -t %s"%(home_file,jupiter_config.STREAM_IMAGE)
    os.system(cmd)
    os.system("sudo docker push " + jupiter_config.STREAM_IMAGE )

    # os.system("rm *.Dockerfile")

def build_push_streams():
    """Build STREAMer home image from Docker files and push them to the Dockerhub.
    """

    port_list_home = prepare_global_info()
    import streams_docker_files_generator as dc 

    os.chdir(jupiter_config.STREAMS_PATH)
    logging.debug(os. getcwd())

    app_config = load_app_config()
    datasources = parse_datasources(app_config)


    for name in datasources:
        logging.debug('Building data sources image '+name)
        home_file = dc.write_stream_home_docker(username = jupiter_config.USERNAME,
                          password = jupiter_config.PASSWORD,
                          app_file = jupiter_config.APP_NAME,
                          ports = " ".join(port_list_home),
                          datasource = datasources[name]['dataset'])
        #--no-cache
        cmd = "sudo docker build -f %s ../.. -t %s"%(home_file,datasources[name]['stream_image'])
        os.system(cmd)
        os.system("sudo docker push " + datasources[name]['stream_image'])

    # os.system("rm *.Dockerfile")
if __name__ == '__main__':
    # build_push_streams()
    build_push_stream()

