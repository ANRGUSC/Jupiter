import logging
import os
import time

logging.basicConfig(level=logging.ERROR)

NUM_RETRIES = 100

# warning: not all containers have these environment variables
def profiler_id_to_ip(id):
    profilers_ips = os.environ['ALL_PROFILERS_IPS'].split(':')
    allprofiler_names = os.environ['ALL_PROFILERS_NAMES'].split(':')
    profilers_ips = profilers_ips[1:]
    combined_ip_map = dict(zip(allprofiler_names, profilers_ips))
    ip = combined_ip_map[id]
    return ip

# warning: not all containers have these environment variables
def nodeid_to_ip(id):
    node_ips = os.environ['ALL_NODES_IPS'].split(':')
    node_ids = os.environ['ALL_NODES'].split(':')
    node_ips = node_ips[1:]
    combined_ip_map = dict(zip(node_ids, node_ips))
    ip = combined_ip_map[id]
    return ip

def transfer_data_scp(ip, port, user, pw, src, dst):
    # Keep retrying in case the containers are still building/booting up on
    # the child nodes.
    retry = 0
    while retry < NUM_RETRIES:
        try:
            cmd = "sshpass -p %s scp -P %s -o StrictHostKeyChecking=no -r %s %s@%s:%s" \
                % (pw, port, src, user, ip, dst)
            os.system(cmd)
            logging.debug('data transfer complete\n')
            break
        except:
            logging.debug('transfer_data_scp: retrying...')
            time.sleep(2)
            retry += 1

    if retry == NUM_RETRIES:
        logging.error("transfer_data_scp: unable to send file")
