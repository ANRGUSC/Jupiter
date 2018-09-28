__author__ = "Quynh Nguyen, Aleksandra Knezevic and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import re
  
 
def task(filename, pathin, pathout):
 
 
    print(filename)
    input_path = os.path.join(filename.split('/')[-1],filename)
    output3 = filename.split('_')[0] +'_task3.txt'
    pathout = '/centralized_scheduler/output/'
    output_path = os.path.join(pathout, output3)

    print(input_path)
    print(output_path)
 
    file_output = open(output_path, 'w')
 
    print(input_path)
    print(file_output)

    data = []
    with open(input_path,'r') as file_input:
        for line in file_input:
            data = line.strip().split(' ')
            data = sorted(data, reverse= True)
            print(data)
            for num in data:
                file_output.write(num+" ")
    
    file_output.close()
    return [output_path]

def main():

    filelist = '25botnet'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile