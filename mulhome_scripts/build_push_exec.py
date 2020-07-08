__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import sys
sys.path.append("../")
import os
import jupiter_config
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)


def build_push_exec():
    """
    Build execution profiler home and worker image from Docker files and push
    them to Dockerhub.
    """

    jupiter_config.set_globals()
    port_list = jupiter_config.get_ports()
    logging.debug('build_push_exec: ports to expose for all containers are {}'
                  .format(" ".join(port_list)))
    import execution_profiler.dockerfile_generator as gen

    home_file = gen.write_exec_home_docker(
        username=jupiter_config.USERNAME,
        password=jupiter_config.PASSWORD,
        app_dir=jupiter_config.APP_NAME,
        ports=" ".join(port_list)
    )

    worker_file = gen.write_exec_worker_docker(
        username=jupiter_config.USERNAME,
        password=jupiter_config.PASSWORD,
        app_dir=jupiter_config.APP_NAME,
        ports=" ".join(port_list)
    )

    # copy all files needed from working directory into a temp build folder
    shutil.rmtree("./execution_profiler/build/")  # rm existing build folder
    os.makedirs("./execution_profiler/build", exist_ok=True)
    # APP_NAME is really the app path from top dir
    app_dir = jupiter_config.APP_NAME
    shutil.copytree("../{}".format(app_dir),
                    "execution_profiler/build/{}".format(app_dir))
    shutil.copy("../jupiter_config.ini", "execution_profiler/build/")
    shutil.copy("../nodes.txt", "execution_profiler/build/")

    print(jupiter_config.get_exec_home_tag())
    print(jupiter_config.get_exec_worker_tag())

    # pipe Dockerfile template into `docker build` via stdin
    os.system("echo \"{}\" | docker build -t {} -f - ./execution_profiler"
              .format(home_file, jupiter_config.get_exec_home_tag()))
    os.system("docker push {}".format(jupiter_config.get_exec_home_tag()))

    os.system("echo \"{}\" | docker build -t {} -f - ./execution_profiler"
              .format(worker_file, jupiter_config.get_exec_worker_tag()))
    os.system("docker push {}"
              .format(jupiter_config.get_exec_worker_tag()))


if __name__ == '__main__':
    build_push_exec()
