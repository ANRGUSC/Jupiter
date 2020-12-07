__author__ = "Quynh Nguyen, Pradipta Ghosh, Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import os
import logging
import shutil
from jupiter_utils import app_config_parser

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

    tag = app_config.get_mapper_tag()

    # speed up build using existing image
    #os.system("docker pull {}".format(tag))

    os.system(
        "docker build -t {} -f task_mapper/wave/wave.Dockerfile "
        .format(tag) + "./task_mapper/wave"
    )
    os.system("docker push {}".format(tag))


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

    if app_config.task_mapper() == "heft" or "heft_balanced":
        logging.debug('heft')
        build_push_heft(app_config, app_dir)
    elif app_config.task_mapper() == "wave":
        logging.debug('wave')
        build_push_wave(app_config, app_dir)
    else:
        log.error("Unrecognized mapper in app_config.yaml")
