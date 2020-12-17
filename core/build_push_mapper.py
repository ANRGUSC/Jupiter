__author__ = "Quynh Nguyen, Pradipta Ghosh, Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import os
import logging
import shutil
from jupiter_utils import app_config_parser
import threading
import signal

import sys
sys.path.append("../")
import jupiter_config

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def build_push_heft(app_config, app_dir):
    # copy all files needed from Jupiter and from the application into a build
    # folder which will be shipped in the Docker container
    shutil.rmtree("./task_mapper/heft/build/", ignore_errors=True)  # rm existing build folder
    os.makedirs("./task_mapper/heft/build", exist_ok=True)
    shutil.copytree("{}".format(app_dir),
                    "task_mapper/heft/build/app_specific_files/")
    shutil.copy("../jupiter_config.ini", "task_mapper/heft/build/")
    shutil.copytree("./jupiter_utils/",
                    "task_mapper/heft/build/jupiter_utils/")

    tag = app_config.get_mapper_tag()

    # speed up build using existing image
    #os.system("docker pull {}".format(tag))

    os.system(
        "docker build -t {} -f task_mapper/heft/heft.Dockerfile "
        .format(tag) + "./task_mapper/heft"
    )
    os.system("docker push {}".format(tag))

def build_push_home(tag):
    # speed up build using existing image
    # os.system("docker pull {}".format(tag))

    # build and push in execution_profiler/ directory
    err = os.system(
        "docker build -t {} -f task_mapper/wave/wave_home.Dockerfile "
        .format(tag) + "./task_mapper/wave"
    )
    if err != 0:
        log.fatal("home container build failed!")
        os.kill(os.getpid(), signal.SIGKILL)
    os.system("docker push {}".format(tag))


def build_push_worker(tag):
    # speed up build using existing image
    # os.system("docker pull {}".format(tag))

    # build and push in execution_profiler/ directory
    err = os.system(
        "docker build -t {} -f task_mapper/wave/wave_worker.Dockerfile "
        .format(tag) + "./task_mapper/wave"
    )
    if err != 0:
        log.fatal("worker container build failed!")
        os.kill(os.getpid(), signal.SIGKILL)
    os.system("docker push {}".format(tag))

def build_push_wave(app_config, app_dir):
    # copy all files needed from Jupiter and from the application into a build
    # folder which will be shipped in the Docker container
    shutil.rmtree("./task_mapper/wave/build/", ignore_errors=True)  # rm existing build folder
    os.makedirs("./task_mapper/wave/build", exist_ok=True)
    shutil.copytree("{}".format(app_dir),
                    "task_mapper/wave/build/app_specific_files/")
    shutil.copy("../jupiter_config.ini", "task_mapper/wave/build/")
    shutil.copytree("./jupiter_utils/",
                    "task_mapper/wave/build/jupiter_utils/")

    t1 = threading.Thread(target=build_push_home,
                          args=(app_config.get_wave_home_tag(),))
    t2 = threading.Thread(target=build_push_worker,
                          args=(app_config.get_wave_worker_tag(),))

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
        log.error("usage: python build_push_heft.py {APP_NAME}")
        exit()

    app_config = app_config_parser.AppConfig(app_dir)
    mapper_type = app_config.task_mapper().strip()
    if mapper_type == "heft" or mapper_type =="heft_balanced":
        log.debug('heft')
        build_push_heft(app_config, app_dir)
    elif mapper_type == "wave":
        log.debug('wave')
        build_push_wave(app_config, app_dir)
    else:
        log.error("Unrecognized mapper in app_config.yaml")
