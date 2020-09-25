#!/bin/bash

usr="ubuntu"

if [ $1 = "master" ] 
then
        ssh -i id_rsa $usr@178.128.8.175
fi
