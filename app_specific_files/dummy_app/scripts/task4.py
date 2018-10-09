__author__ = "Quynh Nguyen, Aleksandra Knezevic and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import re

def task(filename, pathin, pathout):
 

    if not isinstance(filename, (list)):
        filename = [filename]
    file_name = filename[0].split('_')[0]
    output4 = file_name+'_task4.txt'
   
    input_path1 = os.path.join(pathin,filename[0])
    input_path2 = os.path.join(pathin,filename[1])
    path_output=os.path.join(pathout, output4)
 
    file_output = open(path_output, 'w')
 
    
    

    with open(input_path1, 'r') as file_input:
        for line in file_input:
            file_output.write(line)
            file_output.write("Task 4 has processed the file\n")
    
    with open(input_path2, 'r') as file_input:
        for line in file_input:
            file_output.write(line)
            file_output.write("Task 4 has processed the file\n")


    file_output.close()
    return [path_output]

def main():

    filelist = '25botnet'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile