#!/bin/bash

usr="ubuntu"

if [ $1 = "master" ] 
then
        ssh -i id_rsa $usr@178.128.1.217
elif [ $1 = "n0" ] 
then
        ssh -i id_rsa $usr@64.225.35.82
elif [ $1 = "n1" ]
then
        ssh -i id_rsa $usr@64.225.35.244
elif [ $1 = "n2" ]
then
        ssh -i id_rsa $usr@64.227.50.241
elif [ $1 = "n3" ]
then
        ssh -i id_rsa $usr@64.227.95.123
elif [ $1 = "n4" ]
then
        ssh -i id_rsa $usr@157.245.165.251
elif [ $1 = "n5" ]
then
        ssh -i id_rsa $usr@165.232.53.81
elif [ $1 = "n6" ]
then
        ssh -i id_rsa $usr@167.172.222.56
elif [ $1 = "n7" ]
then
        ssh -i id_rsa $usr@167.172.204.65
elif [ $1 = "n8" ]
then
        ssh -i id_rsa $usr@142.93.9.255
elif [ $1 = "n9" ]
then
        ssh -i id_rsa $usr@204.48.20.181
elif [ $1 = "n10" ]
then
        ssh -i id_rsa $usr@161.35.118.97
elif [ $1 = "n11" ]
then
        ssh -i id_rsa $usr@204.48.22.38
elif [ $1 = "n12" ]
then
        ssh -i id_rsa $usr@46.101.198.62
elif [ $1 = "n13" ]
then
        ssh -i id_rsa $usr@46.101.167.187
elif [ $1 = "n14" ]
then
        ssh -i id_rsa $usr@46.101.198.49
fi
