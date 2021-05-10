# paste the output to app_config.yaml
i = 1
r = open('nodes.txt', 'r')
line = ""
'''
while(1):
    line = r.readline()
    if line == "":
        break
    line = line.rstrip('\n')
    print("node" + str(i) + ": " + line.split(' ')[1])
    i += 1
r.close()
'''

while(1):
    line = r.readline()
    if line == "":
        break
    line = line.rstrip('\n')
    st = line.split(' ')[1]
    print("    - name: datasource" + str(i))
    print("      base_script: datasource.py")
    print("      k8s_host: "+st)
    print("      children: master")
    i += 1
