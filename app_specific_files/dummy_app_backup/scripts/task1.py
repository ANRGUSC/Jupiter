__author__ = "Quynh Nguyen, Aleksandra Knezevic and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import re
  
 
def task(filename, pathin, pathout):
 
 
    #output1 = filename.replace('.txt','') +"_1"
    file_name = filename.split('.')[0]
    output1 = file_name+'_task1.txt'

    input_path = os.path.join(pathin, filename)
    output_path = os.path.join(pathout, output1)


    file_output = open(output_path, 'w')

    print('**********************')
    print(input_path)
    print(file_output)
    with open(input_path, 'r') as file_input:
        for line in file_input:
            for n in line.strip().split(" "):
                num=int(n) 
                print(num)
                if num%2==0:

                    line = re.sub(re.compile(n+" *"),"", line)+ "\n"
                    print(line)
                    file_output.write(line)

    file_output.close()
    return [output_path]

def main():

    filelist = '25botnet.ipsum'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile