
hosts_file_ip_line = [2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,21,22,23,24,25,26,27,28,29,30,31,32,33,34]
ips = []
def is_ip_char(c):

    return (c >= '0' and c <= '9') or c == '.'

r = open('node_ips', 'r')
line = ""
while(1):
    line = r.readline()
    if line == "":
        break
    line = line.rstrip('\n')
    ips.append(line)
r.close()


with open('hosts', 'r') as file:
    # read a list of lines into data
    data2 = file.readlines()
for line_num in hosts_file_ip_line:
    line = data2[line_num-1].rstrip('\n')
    index = len(line)-1
    while line[index] != '=':
        index -= 1
    index += 1
    new_line = line[:index]
    new_line += ips[hosts_file_ip_line.index(line_num)]
    new_line += "\n"
    new_line = new_line.replace('root', 'ubuntu')
    data2[line_num-1] = new_line
with open('hosts', 'w') as file:
    file.writelines( data2 )

