# paste the output to app_config.yaml
i = 1
with open('nodes_list.txt', 'r') as r:
    line = ""
    while True:
        line = r.readline()
        if line == "":
            break
        line = line.rstrip('\n')
        print("node" + str(i) + ": " + line.split(' ')[0])
        i += 1
