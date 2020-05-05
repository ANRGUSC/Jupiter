"""
bottleneck is a link, src node proc1, dst node proc2, 
all nodes containing parent tasks of any task on src: par1, par2, ..., parK
for a given set of idle nodes, try duplicating all proc1 tasks on each one
improvement condition: max(COMM(parentN->cand) + COMP(all tasks on cand) + COMM(cand->dst)) < 


"""
def 
