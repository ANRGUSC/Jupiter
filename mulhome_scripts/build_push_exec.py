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

    # copy all files needed from working directory into a temp build folder
    shutil.rmtree("./execution_profiler/build/")  # rm existing build folder
    os.makedirs("./execution_profiler/build", exist_ok=True)
    # APP_NAME is really the app path from top dir
    app_dir = jupiter_config.APP_NAME
    shutil.copytree("../{}".format(app_dir),
                    "execution_profiler/build/app_specific_files")
    shutil.copy("../jupiter_config.ini", "execution_profiler/build/")
    shutil.copy("../nodes.txt", "execution_profiler/build/")
    shutil.copytree("./jupiter_utils/",
                    "execution_profiler/build/jupiter_utils/")

    # build and push in execution_profiler/ directory
    # TODO: optimize by parallelizing building of containers
    os.system(
        "docker build -t {} -f execution_profiler/exec_profiler_home.Dockerfile "
        .format(jupiter_config.get_exec_home_tag()) +
        "./execution_profiler"
    )
    os.system("docker push {}".format(jupiter_config.get_exec_home_tag()))

    os.system(
        "docker build -t {} -f execution_profiler/exec_profiler_worker.Dockerfile "
        .format(jupiter_config.get_exec_worker_tag()) +
        "./execution_profiler"
    )
    os.system("docker push {}".format(jupiter_config.get_exec_worker_tag()))

if __name__ == '__main__':
    build_push_exec()
