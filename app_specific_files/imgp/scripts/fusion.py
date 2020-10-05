"""
 * Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh, March 2019
 *      Wenda Chen, March 2019
 *      Bhaskar Krishnamachari, March 2019
 *     Read license file in main directory for more details
"""

import os
import time
import cv2 as cv
import csv

def task(filelist, pathin, pathout):

    output_files = filelist[0].split('/')[-1].split(".")[0].split('_')[0] + "_fusion.csv"
    
    with open(os.path.join(pathout, output_files),"wt") as res:
        cw = csv.writer(res);
        cw.writerow(["Type","X","Y","Xlength","Ylength"])
        with open(os.path.join(pathin,filelist[0]),"rt") as f:
            cr = csv.reader(f);
            for line in cr:
                #the first column 0 stands for human rectangles
                line.insert(0,"0")
                cw.writerow(line)    
        with open(os.path.join(pathin,filelist[1]),"rt") as f:
            cr = csv.reader(f);
            for line in cr:
                #the first column 1 stands for human rectangles
                line.insert(0,"1")
                cw.writerow(line)    
    
    return [os.path.join(pathout, output_files)]



def main():
    filelist= ['test_human.csv', 'test_car.csv']
    outpath = os.path.join(os.path.dirname(__file__), "sample_input/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':

    filelist= ['test_human.csv', 'test_car.csv']
    task(filelist, '/home/zxc/Desktop/imgptest/generated_files', '/home/zxc/Desktop/imgptest/generated_files')

