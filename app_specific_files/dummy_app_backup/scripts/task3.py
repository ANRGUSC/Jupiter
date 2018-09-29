__author__ = "Quynh Nguyen, Aleksandra Knezevic and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import re
  
 
def task(filename, pathin, pathout):
 
 
    #output3 = filename.replace('.txt','')+"_3"
    file_name = filename.split('_')[0]
    output3 = file_name+'_task3.txt'
    input2 = file_name+'_task1.txt'
     
    input_path = os.path.join(pathin, input2)
    output_path = os.path.join(pathout, output3)
 
    file_output = open(output_path, 'w')
 
    print('**********************')
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