"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""
import sys
sys.path.append("../")

import jupiter_config
import os

sys.path.append(jupiter_config.NETR_PROFILER_PATH)
import profiler_docker_files_generator as dc
port_list = []
port_list.append(jupiter_config.SSH_DOCKER)
port_list.append(jupiter_config.MONGO_DOCKER)
port_list.append(jupiter_config.FLASK_DOCKER)
print('The list of ports to be exposed in the profiler dockers are ', " ".join(port_list))

def build_push_profiler():

    os.chdir(jupiter_config.NETR_PROFILER_PATH)

    dc.write_profiler_home_docker(username = jupiter_config.USERNAME,
                     password = jupiter_config.PASSWORD,
                     ports = " ".join(port_list))

    dc.write_profiler_worker_docker(username = jupiter_config.USERNAME,
                     password = jupiter_config.PASSWORD,
                     ports = " ".join(port_list))


    os.system("sudo docker build -f profiler_home.Dockerfile ../.. -t "
                                 + jupiter_config.PROFILER_HOME_IMAGE)
    os.system("sudo docker push " + jupiter_config.PROFILER_HOME_IMAGE)

    os.system("sudo docker build -f profiler_worker.Dockerfile ../.. -t "
                                 + jupiter_config.PROFILER_WORKER_IMAGE)
    os.system("sudo docker push " + jupiter_config.PROFILER_WORKER_IMAGE)

if __name__ == '__main__':
    build_push_profiler()
