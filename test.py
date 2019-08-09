# schedule = {'task23': 'node3', 'task22': 'node3', 'task21': 'node3', 'task20': 'node3', 'task27': 'node3', 'task26': 'node3', 'task25': 'node3', 'task24': 'node3', 'task29': 'node3', 'task28': 'node3', 'task0': 'node3', 'task1': 'node3', 'task2': 'node3', 'task3': 'node3', 'task4': 'node3', 'task5': 'node3', 'task6': 'node3', 'task7': 'node3', 'task8': 'node3', 'task9': 'node3', 'task30': 'node3', 'task18': 'node3', 'task19': 'node3', 'task12': 'node3', 'task13': 'node3', 'task10': 'node3', 'task11': 'node3', 'task16': 'node3', 'task17': 'node3', 'task14': 'node3', 'task15': 'node3'}


# count = dict()
# e = []
# for task in schedule:
#     e.append(task)
#     if schedule[task] not in count:
#         count[schedule[task]] = 1
#     else:
#         count[schedule[task]] = count[schedule[task]] + 1

# print(count)
# a = max(count, key=count.get)
# print(a)
# print(count[a])
# e.sort()
# print(e)

exec_time = {'10botnet.ipsum': 48.02594470977783, '5botnet.ipsum': 48.203089475631714, '2botnet.ipsum': 49.417967081069946, '9botnet.ipsum': 49.78686451911926, '1botnet.ipsum': 48.21839356422424, '4botnet.ipsum': 48.53897285461426, '7botnet.ipsum': 48.21215057373047, '3botnet.ipsum': 46.91892051696777, '8botnet.ipsum': 48.327016830444336, '6botnet.ipsum': 47.775649070739746}

s = 0 
c = 0
for file in exec_time:
	print(c)
	if c==5:
		s=0
	s = s+exec_time[file]
	if c==4 or c==9:
		print(s/5)
	c = c+1





