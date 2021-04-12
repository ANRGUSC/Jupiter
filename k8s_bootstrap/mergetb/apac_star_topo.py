import mergexp as mx
from mergexp.net import capacity, latency, routing, static, addressing, ipv4
from mergexp.machine import memory,image,cores
from mergexp.unit import gb,mbps, ms

# set number of minnow worker nodes
NUM_MINNOWS = 360

# set number of rohu worker nodes
NUM_ROHUS = 144

net = mx.Topology('lanoflan', routing == static, addressing == ipv4)
depth = 7
lannum = 8
nodenum = 9
hub = net.device('hub', memory >= gb(8))

def ubuntu(name, version, min_memory=2):
    dev = net.device(name, image == "ubuntu:" + version,
                     memory >= gb(min_memory))
    dev.props['group'] = version
    return dev

total_worker_nodes = NUM_MINNOWS + NUM_ROHUS

master = net.device("master", memory >= gb(40))
master.props["shape"] = "wye"
master.props["color"] = "red"

JUPITER_MASTER_NODE = ["master"] 
JUPITER_WORKER_NODES = []

for d in range(2):
    root = net.device(f'hub-{d}', memory >= gb(8))
    net.connect([root, hub])
    for l in range(lannum):
        nodes = [ubuntu(f"node{d}-{l}-{n}", '1804', 4) for n in range(nodenum)]
        JUPITER_WORKER_NODES.extend("node%d-%d-%d"%(d,l,n) for n in range(nodenum))
        net.connect([root] + nodes)
for d in range(2,depth):
    root = net.device(f'hub-{d}', memory >= gb(8))
    net.connect([root, hub])
    for l in range(lannum):
        nodes = [ubuntu(f"node{d}-{l}-{n}", '1804', 1) for n in range(nodenum)]
        JUPITER_WORKER_NODES.extend("node%d-%d-%d"%(d,l,n) for n in range(nodenum))
        net.connect([root] + nodes) 

net.connect([master,hub]) 
mx.experiment(net)
