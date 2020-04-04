__author__ = "Quynh Nguyen, Pradipta Ghosh,  Pranav Sakulkar,  Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

import sys
sys.path.append("../")
import os
import configparser
import jupiter_config
import logging

logging.basicConfig(level = logging.DEBUG)


def build_push_stress():
	jupiter_config.set_globals()
    INI_PATH  = jupiter_config.APP_PATH + 'app_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    sys.path.append(jupiter_config.SIM_STRESS)
    logging.debug(jupiter_config.SIM_STRESS)
    os.chdir(jupiter_config.SIM_STRESS)
    stress_file = 'Dockerfile'
    cmd = "sudo docker build -f %s ../../ -t %s"%(stress_file,jupiter_config.STRESS_IMAGE)
    os.system(cmd)
    os.system("sudo docker push " + jupiter_config.STRESS_IMAGE)


if __name__ == '__main__':
	build_push_stress()	
