__author__ = "Pradipta Ghosh, Pranav Sakulkar, Quynh Nguyen, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import logging
import shutil
import subprocess
import argparse
from pathlib import Path

import sys
sys.path.append("../")
import jupiter_config
from jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

build_failed = False


def build_push(tag):
    global build_failed
    result = subprocess.run(
        ["docker", "build", "-t", tag,
         "-f", "circe/Dockerfile",
         "./circe"],
        check=False
    )
    if result.returncode != 0:
        log.fatal("CIRCE container build failed!")
        build_failed = True
        return
    push = subprocess.run(["docker", "push", tag], check=False)
    if push.returncode != 0:
        log.fatal("CIRCE container push failed!")
        build_failed = True


def main(app_dir):
    """
    Build CIRCE image from Docker files and push them to Dockerhub.
    """
    app_config = app_config_parser.AppConfig(app_dir)

    build_dir = Path("./circe/build")
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(app_dir, build_dir / "app_specific_files")
    shutil.copy("../jupiter_config.ini", build_dir)
    shutil.copytree("./jupiter_utils/", build_dir / "jupiter_utils")

    # Copy app's requirements.txt only if modified to prevent unnecessary pip reinstalls
    req_dir = Path("./circe/build_requirements")
    req_dir.mkdir(parents=True, exist_ok=True)
    src = Path(app_dir) / "requirements.txt"
    dst = req_dir / "requirements.txt"
    try:
        mtime = dst.stat().st_mtime
    except FileNotFoundError:
        mtime = 0
    if src.stat().st_mtime - mtime > 1:
        shutil.copy(src, dst)

    build_push(app_config.get_circe_tag())

    if build_failed:
        log.error("One or more build/push steps failed.")
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Build and push CIRCE Docker image."
    )
    parser.add_argument(
        "app_name", nargs="?",
        help="App name (directory under ${JUPITER_ROOT}/app_specific_files/)"
    )
    args = parser.parse_args()

    if args.app_name:
        app_dir = "../app_specific_files/{}".format(args.app_name)
        log.info("Setting app directory to: {}".format(app_dir))
    else:
        log.info("Defaulting to jupiter_config.py to set app directory.")
        app_dir = jupiter_config.get_abs_app_dir()
        log.info("Setting app directory to: {}".format(app_dir))

    main(app_dir)
