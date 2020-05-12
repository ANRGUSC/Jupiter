"""
duplication and split can both remove link bottlenecks, but only split can remove comp btnk
duplication is doing some tasks twice, and incurred multiple link usage to make btnk link completely idle
split can evenly distribute jobs on more reources without redundent work
one good point of duplication though, is that it can bypass a link, which could be bad
Some points:
1. the new node should duplicate all (not some) tasks assigned to original node
2. a node can have as many dup nodes, which will indefinately increase throughput
3. should set a bound on max number of idle nodes to use, can use two for now
4. how to calculate the portion of each nodes' work? 
     old node/links drop below btnk (it will always drop though, as long as portion < 1, because it is the btnk)
     new node/links don't become btnk. a simple way is to calculate the btnk of the par->cur->child path,
     and the par->new->child path, and assign portions so as to make them the same
------------------------ condition under which to use split --------------------------------

"""
