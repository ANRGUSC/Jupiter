import mergexp as mx

net = mx.Topology('hello')

JUPITER_MASTER_NODES = ["master"]
JUPITER_WORKER_NODES = ["n1", "n2","n3","n4","n5"]

ALL_NODES = JUPITER_MASTER_NODES + JUPITER_WORKER_NODES
# replace me with your experiment topology
nodes = [net.device(name) for name in ALL_NODES]
net.connect(nodes)

mx.experiment(net)
