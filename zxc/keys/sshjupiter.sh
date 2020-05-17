#!/bin/bash

if [ $1 = "master" ] 
then
	ssh -i id_rsa ubuntu@178.128.15.126
elif [ $1 = "node1" ] 
then
        ssh -i id_rsa ubuntu@64.225.31.59
elif [ $1 = "node2" ]
then
        ssh -i id_rsa ubuntu@64.225.31.60
elif [ $1 = "node3" ]
then
        ssh -i id_rsa ubuntu@64.225.37.64
elif [ $1 = "node4" ]
then
        ssh -i id_rsa ubuntu@165.227.63.0
elif [ $1 = "node5" ]
then
        ssh -i id_rsa ubuntu@159.65.108.245
elif [ $1 = "node6" ]
then
        ssh -i id_rsa ubuntu@64.227.54.51
elif [ $1 = "node7" ]
then
        ssh -i id_rsa ubuntu@64.227.58.234
fi

