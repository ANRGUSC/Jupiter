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

def task(input_files, pathin, pathout):

    onefile = input_files
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

    output_files = image_path.split('/')[-1].split(".")[0].split('_')[0] + "_car.csv"
    with open(os.path.join(pathout, output_files), "wt") as f:
        cw = csv.writer(f)
        for x, y, w, h in cars:
            cw.writerow([x,y,w,h])

    return [os.path.join(pathout, output_files)]




def main():
    filelist= 'test_merged.jpeg'
    outpath = os.path.join(os.path.dirname(__file__), "sample_input/")
    outfile = task(filelist, outpath, outpath)
    return outfile


if __name__ == '__main__':

    filelist= 'test_merged.jpeg'
    task(filelist, '/home/zxc/Desktop/imgptest/generated_files', '/home/zxc/Desktop/imgptest/generated_files')




