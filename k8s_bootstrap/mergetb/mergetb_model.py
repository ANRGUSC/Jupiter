import mergexp as mx
from mergexp.machine import image
from mergexp.net import addressing, ipv4
from mergexp.machine import cores, memory
from mergexp.unit import gb

# set number of worker nodes
NUM_WORKER_NODES = 4

# minimum memory for all nodes, current DCOMP nodes include either 2GB or 8GB
MIN_MEMORY = 4


def ubuntu(name, version, min_memory=2):
    dev = net.device(name, image == "ubuntu:" + version,
                     memory >= gb(min_memory))
    dev.props['group'] = version
    return dev


net = mx.Topology('k8s-bootstrap-example', addressing == ipv4)

JUPITER_MASTER_NODES = ["master"]
JUPITER_WORKER_NODES = ["n%d" % (x) for x in range(0, NUM_WORKER_NODES)]
ALL_NODES = JUPITER_MASTER_NODES + JUPITER_WORKER_NODES
nodes = [ubuntu(name, '1804', MIN_MEMORY) for name in ALL_NODES]
net.connect(nodes)

mx.experiment(net)
