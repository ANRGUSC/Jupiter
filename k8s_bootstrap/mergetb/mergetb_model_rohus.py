import mergexp as mx
from mergexp.machine import cores, memory
from mergexp.unit import gb

net = mx.Topology('hello')

JUPITER_MASTER_NODES = ["master"]
JUPITER_WORKER_NODES = ["n%d"%(x) for x in range(0,10)]
master = net.device('master', memory >= gb(4))
worker_nodes = []
for name in JUPITER_WORKER_NODES:
    worker_nodes.append(net.device(name,memory >= gb(4)))
#worker_nodes = [net.device(name) for name in JUPITER_WORKER_NODES]

net.connect(worker_nodes + [master])

mx.experiment(net)