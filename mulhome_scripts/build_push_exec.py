__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import os
import logging
import shutil
import threading

import sys
sys.path.append("../")
import jupiter_config
from jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def build_push_home(tag):
    # build and push in execution_profiler/ directory
    os.system(
        "docker build -t {} -f execution_profiler/home.Dockerfile "
        .format(tag) + "./execution_profiler"
    )
    os.system("docker push {}".format(tag))


def build_push_worker(tag):
    # build and push in execution_profiler/ directory
    os.system(
        "docker build -t {} -f execution_profiler/worker.Dockerfile "
        .format(tag) + "./execution_profiler"
    )
    os.system("docker push {}".format(tag))


def main(app_dir):
    """
    Build execution profiler home and worker image from Docker files and push
    them to Dockerhub.
    """
    app_config = app_config_parser.AppConfig(app_dir, jupiter_config.APP_NAME)

    # copy all files needed from Jupiter and from the application into a build
    # folder which will be shipped in the Docker container
    shutil.rmtree("./execution_profiler/build/", ignore_errors=True)  # rm existing build folder
    os.makedirs("./execution_profiler/build", exist_ok=True)
    shutil.copytree("{}".format(app_dir),
                    "execution_profiler/build/app_specific_files/")
    shutil.copy("../jupiter_config.ini", "execution_profiler/build/")
    shutil.copytree("./jupiter_utils/",
                    "execution_profiler/build/jupiter_utils/")

    # build in parallel
    t1 = threading.Thread(target=build_push_home,
                          args=(app_config.get_exec_home_tag(),))
    t2 = threading.Thread(target=build_push_worker,
                          args=(app_config.get_exec_worker_tag(),))

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
        log.error("usage: python build_push_exec.py {APP_NAME}")
        exit()

    main(app_dir)
