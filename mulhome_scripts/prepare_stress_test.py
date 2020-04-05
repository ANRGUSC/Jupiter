import sys
sys.path.append("../")
import os
import configparser
import jupiter_config
import logging

logging.basicConfig(level = logging.DEBUG)


def prepare_stress_test():
	jupiter_config.set_globals()
	cmd = "sudo docker pull "+ jupiter_config.STRESS_IMAGE
	os.system(cmd)
	cmd = "sudo docker run -d --name sim "+ jupiter_config.STRESS_IMAGE
	os.system(cmd)
	cmd = "docker exec -it sim python3 /stress_test.py"
	os.system(cmd)
if __name__ == '__main__':
    prepare_stress_test()