#!/bin/bash

usr="ubuntu"

if [ $1 = "master" ] 
then
        ssh -i id_rsa $usr@206.189.173.110
fi
