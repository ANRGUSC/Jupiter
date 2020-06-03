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
    sys.path.append(jupiter_config.STREAM_PRICING_PATH)
    sys.path.append(jupiter_config.STREAMS_PRICING_PATH)
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

def build_push_decoupled_stream():
    """Build STREAMer home image from Docker files and push them to the Dockerhub.
    """

    logging.debug('Building datasources for decoupled pricing')
    port_list_home = prepare_global_info()
    

    os.chdir(jupiter_config.STREAM_PRICING_PATH)
    logging.debug(jupiter_config.STREAM_PRICING_PATH)
    import stream_decoupled_docker_files_generator as dc 

    home_file = dc.write_stream_decoupled_home_docker(username = jupiter_config.USERNAME,
                      password = jupiter_config.PASSWORD,
                      app_file = jupiter_config.APP_NAME,
                      ports = " ".join(port_list_home))

    #--no-cache
    cmd = "sudo docker build -f %s ../.. -t %s"%(home_file,jupiter_config.STREAM_PRICING_IMAGE)
    os.system(cmd)
    os.system("sudo docker push " + jupiter_config.STREAM_PRICING_IMAGE )

    # os.system("rm *.Dockerfile")

def build_push_streams():
    """Build STREAMer home image from Docker files and push them to the Dockerhub.
    """
    logging.debug('Building multiple datasources for original circe')
    port_list_home = prepare_global_info()
    import streams_docker_files_generator as dc 

    os.chdir(jupiter_config.STREAMS_PATH)

    app_path = jupiter_config.APP_NAME 
    app_config_path = "../../" +app_path + "/app_config.yaml"
    app_config = load_app_config(app_config_path)
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

def build_push_decoupled_streams():
    """Build STREAMer home image from Docker files and push them to the Dockerhub.
    """
    logging.debug('Building multiple datasources for original circe')
    port_list_home = prepare_global_info()
    import streams_decoupled_docker_files_generator as dc 

    os.chdir(jupiter_config.STREAMS_PRICING_PATH)
    logging.debug(jupiter_config.STREAMS_PRICING_PATH)

    app_path = jupiter_config.APP_NAME 
    app_config_path = "../../" +app_path + "/app_config.yaml"
    app_config = load_app_config(app_config_path)
    datasources = parse_datasources(app_config)
    logging.debug(datasources)


    for name in datasources:
        logging.debug('Building data sources image '+name)
        logging.debug(datasources[name]['stream_image'])
        home_file = dc.write_streams_decoupled_home_docker(username = jupiter_config.USERNAME,
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
    # Multiple datasets - original circe
    build_push_streams()

    # Single dataset - original circe
    # build_push_stream()

    # Single dataset - pricing circe
    # build_push_decoupled_stream()

    # Multiple datasets - pricing circe
    # build_push_decoupled_streams()
