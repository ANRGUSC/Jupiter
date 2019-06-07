#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script is used entirely for evaluation purpose.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"


import shutil
import os
import random
import time
import glob


def evaluate_random():
    """
    Copy files from folder ``sample_input`` to folder ``input`` at random intervals for evaluation 
    
    """
    file_count = len(os.listdir("sample_input/")) 
    interval = 120
    for i in range(1,file_count+1):
        n = random.randint(1,interval)
        count = 0
        while count<n:
            count = count+1
            time.sleep(1)
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)

def evaluate_interval(interval):
    """
    Copy files from folder ``sample_input`` to folder ``input`` at regular intervals for evaluation 

    Args:
        interval (int): interval time to inject the sample input file
    
    """
    file_count = len(os.listdir("sample_input/")) 
    for i in range(1,file_count+1):
        count = 0
        while count<interval:
            count = count+1
            time.sleep(1)
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)

def evaluate_sequential():
    """
    Copy files from folder ``sample_input`` to folder ``input`` one after another for evaluation 
    
    """
    file_count = len(os.listdir("sample_input/"))
    file_count_out = len(os.listdir("output/"))
    print('---- Generate random input files')
    file_count = 2
    for i in range(1,file_count+1):
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)
        count = 0
        while 1:
            time.sleep(5)
            file_count_out = len(os.listdir("output/"))
            if file_count_out ==  i:
                time.sleep(30)
                break


    print('---- Finish generating sequential input files')

def evaluate_test():
    file_count = len(os.listdir("sample_input/"))
    print(file_count)
    file_count_out = len(os.listdir("output/"))
    print(file_count_out)
    for filepath in glob.iglob('sample_input/*.ipsum'):
        print(filepath)
        filename = filepath.split('/')[1]
        dest = "input/"+filename
        print('---- Generate random input files')
        shutil.copyfile(filepath,dest)
        count = 0
        while 1:
            time.sleep(5)
            file_count_out = len(os.listdir("output/"))
            if file_count_out ==  file_count:
                time.sleep(30)
                break

def evaluate_mcp():
    file_count = len(os.listdir("sample_input/"))
    file_count_out = len(os.listdir("output/"))
    print('---- Generate random input files')
    print(file_count)
    for i in range(0,file_count):
        print(i)
        src1 = "sample_input/c0_Pictures%d%d%d" %(i)
        dest1 = "input/c0_Pictures%d%d%d" %(i)
        src2 = "sample_input/c1_Pictures%d%d%d" %(i)
        dest2 = "input/c1_Pictures%d%d%d" %(i)
        shutil.copyfile(src1,dest1)
        shutil.copyfile(src2,dest2)
        count = 0
        while 1:
            time.sleep(5)
            file_count_out = len(os.listdir("output/"))
            if file_count_out ==  i+1:
                time.sleep(30)
                break


    print('---- Finish generating sequential input files')   

if __name__ == '__main__':
    #evaluate_random()
    time.sleep(60)
    print('Start copying sample files for evaluation')
    evaluate_mcp()
    #evaluate_sequential()
    #evaluate_test()