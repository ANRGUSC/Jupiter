
hosts_file_ip_line = [2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
ssh_file_ip_line = [7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 43, 46, 49, 52]
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


with open('ssh.sh', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
for line_num in ssh_file_ip_line:
    line = data[line_num-1].rstrip('\n')
    index = len(line)-1
    while is_ip_char(line[index]):
        index -= 1
    index += 1
    new_line = line[:index]
    new_line += ips[ssh_file_ip_line.index(line_num)]
    new_line += "\n"
    data[line_num-1] = new_line
with open('ssh.sh', 'w') as file:
    file.writelines( data )


with open('hosts', 'r') as file:
    # read a list of lines into data
    data2 = file.readlines()
for line_num in hosts_file_ip_line:
    line = data2[line_num-1].rstrip('\n')
    index = len(line)-1
    while is_ip_char(line[index]):
        index -= 1
    index += 1
    new_line = line[:index]
    new_line += ips[hosts_file_ip_line.index(line_num)]
    new_line += "\n"
    data2[line_num-1] = new_line
with open('hosts', 'w') as file:
    file.writelines( data2 )

