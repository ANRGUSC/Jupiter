__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")
import os
import configparser
import jupiter_config


def build_push_wave():
    """Build WAVE home and worker image from Docker files and push them to the Dockerhub.
    """
    jupiter_config.set_globals()
    INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    sys.path.append(jupiter_config.WAVE_PATH)
    print(jupiter_config.WAVE_PATH)

    import wave_docker_files_generator as dc 
    os.chdir(jupiter_config.WAVE_PATH)

    home_file = dc.write_wave_home_docker(app_file = jupiter_config.APP_NAME, ports = jupiter_config.FLASK_DOCKER)
    worker_file = dc.write_wave_worker_docker(app_file = jupiter_config.APP_NAME, ports = jupiter_config.FLASK_DOCKER)


    cmd = "sudo docker build -f %s ../../../ -t %s"%(home_file,jupiter_config.WAVE_HOME_IMAGE)
    os.system(cmd)
    os.system("sudo docker push " + jupiter_config.WAVE_HOME_IMAGE)
    
    cmd = "sudo docker build -f %s ../../../ -t %s"%(worker_file,jupiter_config.WAVE_WORKER_IMAGE)
    os.system(cmd)
    os.system("sudo docker push " + jupiter_config.WAVE_WORKER_IMAGE)



if __name__ == '__main__':
    build_push_wave()