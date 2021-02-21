# paste the output to app_config.yaml
i = 1
r = open('nodes_list.txt', 'r')
line = ""
while(1):
    line = r.readline()
    if line == "":
        break
    line = line.rstrip('\n')
    print("node" + str(i) + ": " + line.split(' ')[0])
    i += 1
r.close()
