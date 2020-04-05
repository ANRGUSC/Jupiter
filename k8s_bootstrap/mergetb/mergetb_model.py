import mergexp as mx
from mergexp.machine import image
from mergexp.net import addressing, ipv4


def ubuntu(name, version):
    dev = net.device(name, image=="ubuntu:" + version)
    dev.props['group'] = version
    return dev


net = mx.Topology('k8s-bootstrap-example', addressing == ipv4)

JUPITER_MASTER_NODES = ["master"]
JUPITER_WORKER_NODES = ["n0", "n1", "n2", "n3", "n4", "n5"]

ALL_NODES = JUPITER_MASTER_NODES + JUPITER_WORKER_NODES
# replace me with your experiment topology
nodes = [ubuntu(name, '1804') for name in ALL_NODES]
net.connect(nodes)

mx.experiment(net)
