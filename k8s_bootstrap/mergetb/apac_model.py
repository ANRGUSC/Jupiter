import mergexp as mx
from mergexp.machine import image
from mergexp.net import addressing, ipv4
from mergexp.machine import cores, memory
from mergexp.unit import gb

# set number of minnow worker nodes
NUM_MINNOWS = 50

# set number of rohu worker nodes
NUM_ROHUS = 50


def ubuntu(name, version, min_memory=2):
    dev = net.device(name, image == "ubuntu:" + version,
                     memory >= gb(min_memory))
    dev.props['group'] = version
    return dev


net = mx.Topology('jupiter-100nodes')

# for generating ansible `hosts` file (see host_generator.py)
total_worker_nodes = NUM_MINNOWS + NUM_ROHUS
JUPITER_MASTER_NODE = ["master"] 
JUPITER_WORKER_NODES = ["n%d" % (x) for x in range(0, total_worker_nodes)]

master = net.device(JUPITER_MASTER_NODE[0], memory >= gb(40))
master.props["shape"] = "wye"
master.props["color"] = "red"

nodes = [master]
nodecount = 0
for minnow in range(NUM_MINNOWS):
    nodes.append(ubuntu("n{}".format(nodecount), '1804', 1))
    nodecount += 1

for rohu in range(NUM_ROHUS):
    nodes.append(ubuntu("n{}".format(nodecount), '1804', 4))
    nodecount += 1

# connect all nodes to LAN
net.connect(nodes)

mx.experiment(net)
