"""
 * Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh, March 2019
 *      Wenda Chen, March 2019
 *      Bhaskar Krishnamachari, March 2019
 *     Read license file in main directory for more details
"""

import numpy as np
import time
import os
import cv2
import csv

# decide whether rectangle r is inside q
def inside(r, q):
    rx, ry, rw, rh = r
    qx, qy, qw, qh = q
    return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh


# draw rectangles
def draw_detections(img, rects, thickness = 1):
    for x, y, w, h in rects:
        # the HOG detector returns slightly larger rectangles than the real objects.
        # so we slightly shrink the rectangles to get a nicer output.
        pad_w, pad_h = int(0.15*w), int(0.05*h)
        cv2.rectangle(img, (x+pad_w, y+pad_h), (x+w-pad_w, y+h-pad_h), (0, 255, 0), thickness)


def task(input_files, pathin, pathout):

    onefile = input_files
    # read image
    image_path = os.path.join(pathin, onefile)
    img = cv2.imread(image_path)  


    # use default detector
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector( cv2.HOGDescriptor_getDefaultPeopleDetector() )
    found, w = hog.detectMultiScale(img, winStride=(8,8), padding=(32,32), scale=1.05)


    # filter the founded cars by remove small rectangles which are inside inside other rectangles
    found_filtered = []
    for ri, r in enumerate(found):
        for qi, q in enumerate(found):
            if ri != qi and inside(r, q):
                break
        else:
            found_filtered.append(r)

    output_files = image_path.split('/')[-1].split(".")[0].split('_')[0] + "_human.csv"
    
    with open(os.path.join(pathout, output_files),"wt") as f:
        cw = csv.writer(f)
        for x, y, w, h in found_filtered:
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


