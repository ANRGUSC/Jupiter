"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Quynh Nguyen
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""
import sys
sys.path.append("../")

import os
import jupiter_config

sys.path.append(jupiter_config.HEFT_PATH)
import heft_dockerfile_generator as dc

def build_push_heft():


    os.system("cp " + jupiter_config.APP_PATH + "configuration.txt "
                    + jupiter_config.HEFT_PATH + "dag.txt")

    os.system("cp " + jupiter_config.APP_PATH + "scripts/config.json "
                    + jupiter_config.HEFT_PATH + "config.json")

    os.chdir(jupiter_config.HEFT_PATH)


    dc.write_heft_docker(PASSWORD = 'PASSWORD', ports = '22 5000')

    os.system("sudo docker build -f Dockerfile . -t "
                                 + jupiter_config.HEFT_IMAGE)
    os.system("sudo docker push " + jupiter_config.HEFT_IMAGE)


    os.system("rm dag.txt")
    os.system("rm config.json")
    os.system("rm Dockerfile")


if __name__ == '__main__':
    build_push_heft()