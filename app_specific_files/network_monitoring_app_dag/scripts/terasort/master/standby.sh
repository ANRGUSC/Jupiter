service ssh start

cd "$(dirname "$0")"

# wget http://supergsego.com/apache/hadoop/common/hadoop-2.8.1/hadoop-2.8.1.tar.gz -P ~/
# tar -zxvf ~/hadoop-2.8.1.tar.gz -C ~/

mkdir /root/TeraSort
cp -r * /root/TeraSort/
mkdir /root/TeraSort/Input

cd /root/TeraSort
python3 -u get_child_ips.py 

chmod +x Master-Detection.sh
chmod +x Master-PrepareInput.sh
g++ -std=c++11 extractIPs.cpp -o extractIPs
make
g++ -std=c++11 filterResult.cpp -o filterResult


# while IFS=':' read -ra ADDR; do for i in "${ADDR[@]}"; do echo $i >> ips.txt; done; done <<< "$NODE_IPS"

sleep 30

bash Master-Network.sh 3 ips.txt  # 3 is the number of workers
                               # ips.txt lists the IP of the workers

mkdir -p /root/TeraSort/Intermediate
mkdir -p /root/TeraSort/Output

while true; do sleep 100; done
