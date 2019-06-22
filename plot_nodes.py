import matplotlib.pyplot as plt
node_file = 'nodes.txt'
geo = dict()
with open(node_file) as f:
	lines = f.readlines()
	for line in lines:
		info = line.strip().split(' ')
		tmp = info[1].split('-')[-1][0:3]
		if tmp not in geo:
			geo[tmp] = 1
		else:
			geo[tmp] = geo[tmp]+1
print(geo) 
count = sum(geo.values())
plt.pie([float(v) for v in geo.values()], labels=[str(k) for k in geo.keys()], autopct='%1.0f%%')
title = 'Digital Ocean Node Setting : %d nodes'%(count)
plt.title(title)
plt.show()



