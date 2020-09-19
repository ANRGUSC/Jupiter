"""
 * Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh, March 2019
 *      Wenda Chen, March 2019
 *      Bhaskar Krishnamachari, March 2019
 *     Read license file in main directory for more details
"""

import cv2
import numpy as np
import time
import os
import csv
from os import listdir

def task(onefile, pathin, pathout):


    #store the data&time info
    snapshot_time = onefile.partition('_')[2]
    time.sleep(10)


    #use trained cars XML classifiers
    xml_file = os.path.join(os.path.dirname(__file__),'cars.xml')
    car_cascade = cv2.CascadeClassifier(xml_file)
    # car_cascade = cv2.CascadeClassifier('cars.xml')
    # ************* os.path.join(os.path.dirname(__file__),'cars.xml') ************


    # read the image
    image_path = os.path.join(pathin, onefile)
    print(image_path)
    src = cv2.imread(image_path)


    #detect cars in the video
    cars = car_cascade.detectMultiScale(src, 1.1, 3)

  

    with open(os.path.join(pathout,"car_"+snapshot_time.split(".")[0]+".csv"),"wt") as f:
        cw = csv.writer(f)
        for x, y, w, h in cars:
            cw.writerow([x,y,w,h])


    return [os.path.join(pathout,"car_"+snapshot_time.split(".")[0]+".csv")]




def main():
    filelist= 'merged_20190222.jpeg'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile


if __name__ == '__main__':

    filelist= 'merged_20190222.jpeg'
    task(filelist, '/home/erick/detection_app', '/home/erick/detection_app')



