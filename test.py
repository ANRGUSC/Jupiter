a= {'task23': 'node2', 'task22': 'node2', 'task21': 'node2', 'task20': 'node2', 'task27': 'node2', 'task26': 'node3', 'task25': 'node5', 'task24': 'node10', 'task29': 'node10', 'task28': 'node2', 'task45': 'node5', 'task44': 'node5', 'task47': 'node10', 'task46': 'node5', 'task41': 'node2', 'task40': 'node2', 'task43': 'node5', 'task42': 'node5', 'task49': 'node10', 'task48': 'node5', 'task0': 'node2', 'task1': 'node2', 'task2': 'node2', 'task3': 'node2', 'task4': 'node3', 'task5': 'node2', 'task6': 'node2', 'task7': 'node10', 'task8': 'node2', 'task9': 'node3', 'task34': 'node2', 'task35': 'node10', 'task36': 'node2', 'task37': 'node2', 'task30': 'node5', 'task31': 'node3', 'task32': 'node2', 'task33': 'node2', 'task38': 'node2', 'task39': 'node2', 'task18': 'node5', 'task19': 'node3', 'task50': 'node5', 'task51': 'node5', 'task12': 'node2', 'task13': 'node3', 'task10': 'node10', 'task11': 'node5', 'task16': 'node10', 'task17': 'node2', 'task14': 'node2', 'task15': 'node2'}

c = dict()
for k in a:
	if a[k] not in c:
		c[a[k]] = 1
	else:
		c[a[k]] = c[a[k]]+1
print(c)