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

def build_push_heft():


    # os.system("cp " + jupiter_config.APP_PATH + "configuration.txt "
    #                 + jupiter_config.HEFT_PATH + "DAG.txt")

    # os.system("cp " + jupiter_config.APP_PATH + "input_node.txt "
    #                 + jupiter_config.HEFT_PATH + "input_node.txt")

    os.chdir(jupiter_config.HEFT_PATH)

    os.system("sudo docker build -f Dockerfile . -t "
                                 + jupiter_config.HEFT_IMAGE)
    os.system("sudo docker push " + jupiter_config.HEFT_IMAGE)


    # os.system("rm DAG.txt")
    # os.system("rm input_node.txt")


if __name__ == '__main__':
    build_push_heft()