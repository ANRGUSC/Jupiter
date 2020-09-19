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

    snapshot_time = filelist[0].partition('_')[2]

    with open(os.path.join(pathout,"fusion_"+snapshot_time.split(".")[0]+".csv"),"wt") as res:
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
    

    return [os.path.join(pathout,"fusion_"+snapshot_time.split(".")[0]+".csv")]



def main():
    filelist= ['human_20190222.csv', 'car_20190222.csv']
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':


    filelist= ['human_20190222.csv', 'car_20190222.csv']
    task(filelist, '/home/erick/detection_app', '/home/erick/detection_app')


