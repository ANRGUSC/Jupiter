__author__ = "Quynh Nguyen, Pradipta Ghosh, Pranav Sakulkar, Jason A Tran,  Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import logging
import shutil
import subprocess
import threading
import argparse
from pathlib import Path

import sys
sys.path.append("../")
import jupiter_config
from jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

build_failed = threading.Event()


def build_push_heft(app_config, app_dir):
    build_dir = Path("./task_mapper/heft/build")
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(app_dir, build_dir / "app_specific_files")
    shutil.copy("../jupiter_config.ini", build_dir)
    shutil.copytree("./jupiter_utils/", build_dir / "jupiter_utils")

    tag = app_config.get_mapper_tag()
    result = subprocess.run(
        ["docker", "build", "-t", tag,
         "-f", "task_mapper/heft/heft.Dockerfile",
         "./task_mapper/heft"],
        check=False
    )
    if result.returncode != 0:
        log.fatal("HEFT container build failed!")
        build_failed.set()
        return
    push = subprocess.run(["docker", "push", tag], check=False)
    if push.returncode != 0:
        log.fatal("HEFT container push failed!")
        build_failed.set()


def build_push_home(tag):
    result = subprocess.run(
        ["docker", "build", "-t", tag,
         "-f", "task_mapper/wave/wave_home.Dockerfile",
         "./task_mapper/wave"],
        check=False
    )
    if result.returncode != 0:
        log.fatal("home container build failed!")
        build_failed.set()
        return
    push = subprocess.run(["docker", "push", tag], check=False)
    if push.returncode != 0:
        log.fatal("home container push failed!")
        build_failed.set()


def build_push_worker(tag):
    result = subprocess.run(
        ["docker", "build", "-t", tag,
         "-f", "task_mapper/wave/wave_worker.Dockerfile",
         "./task_mapper/wave"],
        check=False
    )
    if result.returncode != 0:
        log.fatal("worker container build failed!")
        build_failed.set()
        return
    push = subprocess.run(["docker", "push", tag], check=False)
    if push.returncode != 0:
        log.fatal("worker container push failed!")
        build_failed.set()


def build_push_wave(app_config, app_dir):
    build_dir = Path("./task_mapper/wave/build")
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(app_dir, build_dir / "app_specific_files")
    shutil.copy("../jupiter_config.ini", build_dir)
    shutil.copytree("./jupiter_utils/", build_dir / "jupiter_utils")

    t1 = threading.Thread(target=build_push_home,
                          args=(app_config.get_wave_home_tag(),))
    t2 = threading.Thread(target=build_push_worker,
                          args=(app_config.get_wave_worker_tag(),))

    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Build and push task mapper Docker images."
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

    app_config = app_config_parser.AppConfig(app_dir)
    mapper_type = app_config.task_mapper().strip()
    if mapper_type in ("heft", "heft_balanced"):
        log.debug('heft')
        build_push_heft(app_config, app_dir)
    elif mapper_type == "wave":
        log.debug('wave')
        build_push_wave(app_config, app_dir)
    else:
        log.error("Unrecognized mapper in app_config.yaml")
        sys.exit(1)

    if build_failed.is_set():
        log.error("One or more build/push steps failed.")
        sys.exit(1)
