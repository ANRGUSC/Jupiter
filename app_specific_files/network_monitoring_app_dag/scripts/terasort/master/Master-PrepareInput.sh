#!/bin/bash

echo "Staring input preparation"
./extractIPs $1 /root/TeraSort/Intermediate/srcIPs.txt

echo "Source IP -C"
cp /root/TeraSort/Intermediate/srcIPs.txt /root/TeraSort/Intermediate/srcIPs-C.txt

echo "End preparation"