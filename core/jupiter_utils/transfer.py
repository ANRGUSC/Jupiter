import logging
import os
import time

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

NUM_RETRIES = 100


# warning: use only in CIRCE containers
def circe_lookup_ip(task_name):
    if task_name == "home":
        return os.environ['CIRCE_HOME_IP']
    worker_ips = os.environ['CIRCE_TASK_TO_IP'].split(' ')
    for item in worker_ips:
        task, ip = item.split(':')
        if task == task_name:
            return ip

    raise CIRCEIpNotFoundError("Unable to find IP of DAG task")


def circe_lookup_nondag_ip(task_name):
    worker_ips = os.environ['CIRCE_NONDAG_TASK_TO_IP'].split(' ')

    for item in worker_ips:
        task, ip = item.split(':')
        if task == task_name:
            return ip

    raise CIRCEIpNotFoundError("Unable to find IP of non-DAG task")


def transfer_data_scp(ip, port, user, pw, src, dst):
    """ Use sshpass and scp to transfer a file to a remote destination.

    [description]

    Arguments:
        ip {string} -- IP address
        port {string} -- port
        user {string} -- username at remote destination
        pw {string} -- password at remote destination
        src {string} -- path of local file
        dst {string} -- target path at remote destination
    """
    # Keep retrying in case the containers are still building/booting up on
    # the child nodes.
    retry = 0
    cmd = f"sshpass -p {pw} scp -P {port} -o StrictHostKeyChecking=no {src} {user}@{ip}:{dst}"
    log.debug(cmd)
    while retry < NUM_RETRIES:
        err = os.system(cmd)
        if err == 0:
            log.debug("transfer successful!")
            break
        else:
            log.debug('transfer_data_scp: failed, retrying...')
            time.sleep(0.5)
            retry += 1

    if retry == NUM_RETRIES:
        log.error("transfer_data_scp: unable to send file")
