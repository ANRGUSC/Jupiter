__author__ = "Quynh Nguyen, Aleksandra Knezevic and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import re

def task(filename, pathin, pathout):
 
 
    #output4 = filename.replace('.txt','')+"_4"
    print(filename)
    print(len(filename))
    if not isinstance(filename, (list)):
        filename = [filename]
    file_name = filename[0].split('_')[0]
    print(file_name)
    output4 = file_name+'_task4.txt'
    input2 = file_name+'_task2.txt'
    input3 = file_name+'_task3.txt'
 
    path_input=os.path.join(pathin, input2)
    path_output=os.path.join(pathout, output4)
 
    file_output = open(path_output, 'w')
 
    print('**********************')
    print(path_input)
    print(file_output)

    with open(path_input, 'r') as file_input:
        for line in file_input:
            print(line)
            file_output.write(line)
            file_output.write("Task 4 has processed the file\n")
    
    path_input=os.path.join(pathin, input3)
    with open(path_input, 'r') as file_input:
        for line in file_input:
            print(line)
            file_output.write(line)
            file_output.write("Task 4 has processed the file\n")


    file_output.close()
    return [path_output]

def main():

    filelist = '25botnet'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile