__author__ = "Quynh Nguyen, Aleksandra Knezevic and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os

def task(filename, pathin, pathout):
 
 
 
 
    #output2 = filename.replace('.txt','')+"_2"
    
    input_path = os.path.join(pathin,filename)
    output3 = filename.split('_')[0] +'_task2.txt'
    output_path = os.path.join(pathout, output3)
 
    file_output = open(output_path, 'w')

    data = []
    with open(input_path,'r') as file_input:
        for line in file_input:
            data = line.strip().split(' ')
            data = sorted(data)
            for num in data:
                file_output.write(num+" ")
    file_output.close()
    return [output_path]

def main():

    filelist = '25botnet_task1.txt'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile