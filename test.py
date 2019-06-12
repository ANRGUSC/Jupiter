a = dict()
a =  {'task22': 'node25', 'task12': 'node23', 'task53': 'node35', 'task42': 'node25', 'task19': 'node25', 'task49': 'node65', 'task15': 'node82', 'task18': 'node78', 'task13': 'node82', 'task4': 'node35', 'task16': 'node84', 'task47': 'node82', 'task1': 'node78', 'task8': 'node35', 'task26': 'node82', 'task43': 'node25', 'task28': 'node78', 'task31': 'node35', 'task10': 'node65', 'task68': 'node35', 'task57': 'node84', 'task60': 'node65', 'task66': 'node79', 'task17': 'node82', 'task11': 'node84', 'task41': 'node79', 'task9': 'node79', 'task55': 'node65', 'task44': 'node65', 'task45': 'node65', 'task3': 'node21', 'task50': 'node23', 'task58': 'node25', 'task6': 'node35', 'task39': 'node82', 'task29': 'node23', 'task71': 'node65', 'task40': 'node2', 'task59': 'node82', 'task0': 'node2', 'task62': 'node35', 'task7': 'node35', 'task27': 'node23', 'task25': 'node23', 'task5': 'node21', 'task2': 'node21', 'task33': 'node35', 'task48': 'node82', 'task38': 'node78', 'task51': 'node23', 'task24': 'node79', 'task14': 'node82', 'task56': 'node2', 'task21': 'node78', 'task52': 'node78', 'task30': 'node79', 'task34': 'node35', 'task32': 'node84', 'task35': 'node23'}
a = {'task22': 'node25', 'task12': 'node23', 'task53': 'node35', 'task42': 'node25', 'task19': 'node25', 'task49': 'node65', 'task15': 'node82', 'task18': 'node78', 'task13': 'node82', 'task4': 'node35', 'task16': 'node84', 'task47': 'node82', 'task1': 'node78', 'task8': 'node35', 'task26': 'node82', 'task43': 'node25', 'task28': 'node78', 'task31': 'node35', 'task10': 'node65', 'task68': 'node35', 'task57': 'node84', 'task60': 'node65', 'task66': 'node79', 'task17': 'node82', 'task11': 'node84', 'task41': 'node79', 'task9': 'node79', 'task55': 'node65', 'task44': 'node65', 'task45': 'node65', 'task3': 'node21', 'task50': 'node23', 'task58': 'node25', 'task6': 'node35', 'task39': 'node82', 'task29': 'node23', 'task71': 'node65', 'task40': 'node2', 'task59': 'node82', 'task0': 'node2', 'task62': 'node35', 'task7': 'node35', 'task27': 'node23', 'task25': 'node23', 'task5': 'node21', 'task2': 'node21', 'task33': 'node35', 'task48': 'node82', 'task38': 'node78', 'task51': 'node23', 'task24': 'node79', 'task14': 'node82', 'task56': 'node2', 'task21': 'node78', 'task52': 'node78', 'task30': 'node79', 'task34': 'node35', 'task32': 'node84', 'task35': 'node23'}
print(a.keys())
print(len(a.keys()))
print(len(set(a.values())))
print(set(a.values()))

node21 = {'task3': True, 'task5': True, 'task2': True}
node35 = {'task53': True, 'task17': True, 'task31': True, 'task33': True, 'task34': True, 'task18': True, 'task6': True, 'task68': True, 'task62': True, 'task4': True, 'task8': True, 'task16': True, 'task14': True, 'task40': True, 'task43': True, 'task15': True, 'task7': True}
node65 = {'task60': True, 'task55': True, 'task49': True, 'task10': True, 'task52': True, 'task50': True, 'task44': True, 'task45': True, 'task71': True}
node84 = {'task32': True, 'task26': True, 'task57': True, 'task11': True, 'task16': True}
node82 = {'task48': True, 'task13': True, 'task59': True, 'task14': True, 'task26': True, 'task15': True, 'task39': True, 'task47': True, 'task17': True, 'task29': True}
node79 = {'task30': True, 'task41': True, 'task24': True, 'task66': True, 'task9': True}
node25 = {'task44': True, 'task42': True, 'task22': True, 'task45': True, 'task43': True, 'task58': True, 'task19': True}
node23 = {'task34': True, 'task27': True, 'task29': True, 'task31': True, 'task33': True, 'task51': True, 'task35': True, 'task50': True, 'task12': True, 'task25': True}
node2 = {'task0': True, 'task1': True, 'task47': True, 'task40': True, 'task2': True, 'task56': True, 'task5': True}
node78 = {'task52': True, 'task28': True, 'task18': True, 'task21': True, 'task38': True, 'task1': True, 'task7': True, 'task25': True}
print(len(node21))
print(len(node35))
print(len(node65))
print(len(node84))
print(len(node82))
print(len(node79))
print(len(node25))
print(len(node23))
print(len(node2))
print(len(node78))

tasks = {'task31': ['task40', 'task43'], 'task12': ['task20'], 'task62': ['task71', 'task69'], 'task49': ['task61', 'task54'], 'task15': ['task19', 'task21'], 'task18': ['task25'], 'task90': ['task95', 'task94', 'task100'], 'task4': ['task12', 'task8'], 'task1': ['task10', 'task9', 'task7'], 'task47': ['task49', 'task53', 'task56', 'task55'], 'task16': ['task24', 'task27', 'task26'], 'task8': ['task17', 'task18'], 'task94': ['task103', 'task101', 'task104'], 'task69': ['task76', 'task75', 'task78'], 'task43': ['task45'], 'task85': ['task90', 'task92'], 'task52': ['task58', 'task59'], 'task54': ['task63', 'task65'], 'task26': ['task29', 'task32', 'task35'], 'task17': ['task28'], 'task102': ['task106', 'task105'], 'task91': ['task99'], 'task44': ['task52', 'task51'], 'task64': ['task72', 'task73'], 'task7': ['task16', 'task11'], 'task95': ['task102'], 'task84': ['task93', 'task91'], 'task107': ['task111'], 'task70': ['task74'], 'task29': ['task39', 'task38'], 'task36': ['task44'], 'task40': ['task47', 'task48'], 'task75': ['task82'], 'task79': ['task81', 'task86'], 'task59': ['task66', 'task62', 'task68'], 'task78': ['task85', 'task84', 'task87', 'task83'], 'task88': ['task98', 'task97', 'task96'], 'task37': ['task46', 'task41', 'task42'], 'task61': ['task67'], 'task25': ['task33', 'task34', 'task31', 'task30'], 'task100': ['task107', 'task108'], 'task2': ['task4', 'task6'], 'task72': ['task80', 'task79', 'task77'], 'task45': ['task50'], 'task32': ['task37'], 'task50': ['task57', 'task60'], 'task14': ['task22', 'task23'], 'task65': ['task70'], 'task56': ['task64'], 'task6': ['task15', 'task13', 'task14'], 'task30': ['task36'], 'task0': ['task2', 'task1', 'task3', 'task5'], 'task104': ['task110', 'task109'], 'task82': ['task89', 'task88']}
for key in sorted(a.keys()):
    print("%s: %s" % (key, a[key]))

control_relation={'task37': ['task46', 'task41', 'task42'], 'task52': ['task59', 'task58'], 'task102': ['task106', 'task105'], 'task79': ['task81', 'task86'], 'task2': ['task6', 'task8', 'task4'], 'task78': ['task84', 'task87', 'task85'], 'task32': ['task37', 'task36'], 'task18': ['task25', 'task19'], 'task65': ['task70'], 'task74': ['task83'], 'task6': ['task13', 'task15', 'task14'], 'task31': ['task40', 'task43'], 'task1': ['task10', 'task9', 'task7'], 'task69': ['task78', 'task76', 'task75'], 'task50': ['task60', 'task57'], 'task47': ['task56', 'task49', 'task55'], 'task62': ['task71', 'task69'], 'task40': ['task48', 'task47'], 'task8': ['task18', 'task17'], 'task94': ['task101', 'task103', 'task104'], 'task17': ['task28', 'task20'], 'task25': ['task31', 'task34', 'task33', 'task30'], 'task0': ['task1', 'task2', 'task5', 'task3'], 'task104': ['task110', 'task109'], 'task85': ['task92', 'task90'], 'task88': ['task97', 'task98', 'task96', 'task94'], 'task59': ['task68', 'task62', 'task66'], 'task90': ['task100', 'task95'], 'task45': ['task50'], 'task100': ['task108', 'task107'], 'task75': ['task82'], 'task16': ['task24', 'task23', 'task27', 'task22', 'task26'], 'task95': ['task102', 'task99'], 'task82': ['task89', 'task88'], 'task43': ['task45', 'task44'], 'task7': ['task16', 'task11'], 'task70': ['task74'], 'task64': ['task73', 'task72'], 'task49': ['task61', 'task54'], 'task107': ['task111'], 'task26': ['task29', 'task32', 'task35'], 'task54': ['task65', 'task63'], 'task29': ['task39', 'task38'], 'task4': ['task12'], 'task61': ['task67', 'task64'], 'task44': ['task52', 'task53', 'task51'], 'task71': ['task79'], 'task15': ['task21'], 'task72': ['task80', 'task77'], 'task84': ['task91', 'task93']}

for parent_task in control_relation:
	if (parent_task == 'task12') or (parent_task == 'task14') or (parent_task == 'task16'): 
		print('=====')
		print(parent_task)
		for x in control_relation[parent_task]:
			print(x)
		print('=====')