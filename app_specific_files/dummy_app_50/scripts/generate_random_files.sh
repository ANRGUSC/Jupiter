#!/bin/bash
: '
    ** Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Quynh Nguyen, Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

file_path=$1
file_size=$2
echo 'Create file '$file_name
echo 'File size '$file_size
dd if=/dev/urandom of=$file_path bs=1K count=$file_size #KBytes