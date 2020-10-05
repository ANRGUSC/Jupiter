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

def task(input_files, pathin, pathout):

    src = cv.imread(os.path.join(pathin, input_files))
    cv.imwrite(os.path.join(pathout, input_files), src)
    return [os.path.join(pathout, input_files)]



def main():
    filelist= 'test_left.jpeg'
    outpath = os.path.join(os.path.dirname(__file__), "sample_input/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':

    filelist= 'test_left.jpeg'
    task(filelist, '/home/zxc/Desktop/imgptest/sample_input', '/home/zxc/Desktop/imgptest/generated_files')


