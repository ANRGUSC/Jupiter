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


    os.chdir(jupiter_config.HEFT_PATH)

    dc.write_heft_docker(PASSWORD = 'PASSWORD',
                         app_file=jupiter_config.APP_NAME,
                         ports = '22 5000 8888')

    os.system("sudo docker build -f Dockerfile .. -t "
                                 + jupiter_config.HEFT_IMAGE)
    os.system("sudo docker push " + jupiter_config.HEFT_IMAGE)

    os.system("rm Dockerfile")


if __name__ == '__main__':
    build_push_heft()