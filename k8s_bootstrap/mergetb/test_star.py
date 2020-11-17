import mergexp as mx
from mergexp.net import routing, static, addressing, ipv4
from mergexp.machine import memory
from mergexp.unit import gb
net = mx.Topology('lanoflan', routing == static, addressing == ipv4)
depth = 7
lannum = 8
nodenum = 9
hub = net.device('hub', memory >= gb(8))
for d in range(depth):
    root = net.device(f'hub-{d}', memory >= gb(8))
    net.connect([root, hub])
    for l in range(lannum):
        nodes = [net.device(f'node{d}-{l}-{n}') for n in range(nodenum)]
        net.connect([root] + nodes)
mx.experiment(net)