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

def task(filelist, pathin, pathout):

    
    #store the data&time info
    snapshot_time = filelist[0].partition('_')[2]
    time.sleep(10)

    src = cv.imread(os.path.join(pathin, filelist[0]))
    cv.imwrite(os.path.join(pathout,'input1_'+snapshot_time), src)

    src = cv.imread(os.path.join(pathin, filelist[1]))
    cv.imwrite(os.path.join(pathout,'input2_'+snapshot_time), src)
    

    return [os.path.join(pathout,'input1_'+snapshot_time), os.path.join(pathout,'input2_'+snapshot_time)]



def main():
    filelist= ['camera1_20190222.jpeg', 'camera2_20190222.jpeg']
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':

    #Suppose the file structure is erick/detection_app/camera1_input/camera1_20190222.jpeg

    filelist= ['camera1_20190222.jpeg', 'camera2_20190222.jpeg']
    task(filelist, '/home/erick/detection_app/input', '/home/erick/detection_app')


