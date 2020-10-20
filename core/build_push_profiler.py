__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import logging
import shutil
import threading
import signal

import sys
sys.path.append("../")
import jupiter_config
from jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def build_push_home(tag):
    # speed up build using existing image
    os.system("docker pull {}".format(tag))

    # build and push in execution_profiler/ directory
    err = os.system(
        "docker build -t {} -f network_resource_profiler_mulhome/profiler_home.Dockerfile "
        .format(tag) + "./network_resource_profiler_mulhome"
    )
    if err != 0:
        log.fatal("home container build failed!")
        os.kill(os.getpid(), signal.SIGKILL)
    os.system("docker push {}".format(tag))


def build_push_worker(tag):
    # speed up build using existing image
    os.system("docker pull {}".format(tag))

    # build and push in execution_profiler/ directory
    err = os.system(
        "docker build -t {} -f network_resource_profiler_mulhome/profiler_worker.Dockerfile "
        .format(tag) + "./network_resource_profiler_mulhome"
    )
    if err != 0:
        log.fatal("worker container build failed!")
        os.kill(os.getpid(), signal.SIGKILL)
    os.system("docker push {}".format(tag))

def main(app_dir):
    """
    Build execution profiler home and worker image from Docker files and push
    them to Dockerhub.
    """
    app_config = app_config_parser.AppConfig(app_dir)

    # copy all files needed from Jupiter and from the application into a build
    # folder which will be shipped in the Docker container
    shutil.rmtree("./network_resource_profiler_mulhome/build/", ignore_errors=True)  # rm existing build folder
    os.makedirs("./network_resource_profiler_mulhome/build", exist_ok=True)
    shutil.copytree("{}".format(app_dir),
                    "network_resource_profiler_mulhome/build/app_specific_files/")
    shutil.copy("../jupiter_config.ini", "network_resource_profiler_mulhome/build/")
    shutil.copytree("./jupiter_utils/",
                    "network_resource_profiler_mulhome/build/jupiter_utils/")

    # build in parallel
    t1 = threading.Thread(target=build_push_home,
                          args=(app_config.get_drupe_home_tag(),))
    t2 = threading.Thread(target=build_push_worker,
                          args=(app_config.get_drupe_worker_tag(),))

    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == '__main__':

    if len(sys.argv) == 2:
        app_dir = "../app_specific_files/{}".format(sys.argv[1])
        log.info("Setting app directory to: {}"
                     .format(app_dir))
    if len(sys.argv) == 1:
        log.info("Defaulting to jupiter_config.py to set app directory.")
        app_dir = jupiter_config.get_abs_app_dir()
        log.info("Setting app directory to: {}".format(app_dir))
    else:
        log.error("Please insert application name (same name as the app " +
                      "directory under ${JUPITER_ROOT}/app_specific_files/")
        log.error("usage: python build_push_profiler.py {APP_NAME}")
        exit()

    main(app_dir)