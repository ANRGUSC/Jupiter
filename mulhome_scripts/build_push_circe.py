__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import os
import logging
import shutil
import sys

sys.path.append("../")
import jupiter_config
from jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def build_push(tag):
    # speed up build using existing image
    os.system("docker pull {}".format(tag))

    # build and push in circe/original/ directory
    err = os.system(
        "docker build -t {} -f circe/Dockerfile "
        .format(tag) + "./circe"
    )

    if err != 0:
        log.fatal("CIRCE container build failed!")
        exit()

    os.system("docker push {}".format(tag))


def main(app_dir):
    """
    Build execution profiler home and worker image from Docker files and push
    them to Dockerhub.
    """
    app_config = app_config_parser.AppConfig(app_dir)

    # copy all files needed from Jupiter and from the application into a build
    # folder which will be shipped in the Docker container
    shutil.rmtree("./circe/build/", ignore_errors=True)  # rm existing build folder
    os.makedirs("./circe/build", exist_ok=True)
    shutil.copytree("{}".format(app_dir),
                    "circe/build/app_specific_files/")
    shutil.copy("../jupiter_config.ini", "circe/build/")
    shutil.copytree("./jupiter_utils/",
                    "circe/build/jupiter_utils/")

    # Copy app's requirements.txt only if modified to prevent unnecessary pip
    # reinstalls
    os.makedirs("./circe/build_requirements", exist_ok=True)
    src = "{}/requirements.txt".format(app_dir)
    dst = "./circe/build_requirements/requirements.txt"
    try:
        mtime = os.stat(dst).st_mtime
    except FileNotFoundError:
        mtime = 0
    if os.stat(src).st_mtime - mtime > 1:  # modified more than 1s ago
        shutil.copy(src, dst)

    # build in parallel
    build_push(app_config.get_circe_tag())


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
        log.error("usage: python build_push_circe.py {APP_NAME}")
        exit()

    main(app_dir)
