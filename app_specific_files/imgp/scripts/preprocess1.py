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


    filelist=[]
    for onefile in input_files:
        if(onefile.split('.')[0].split('_')[1] == "left"):
            filelist.append(onefile)
    output_files = ""
    
    for filename in filelist:
        print(filename)
        # open the target jpeg and convert to gray scale        
        src = cv.imread(os.path.join(pathin, filename))
        # src = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
        src = cv.resize(src, (480, 320))

        # Histogram Equalization to improve the contrast of image
        #dst = cv.equalizeHist(src)
        
        output_files = filename.split('.')[0] + '_preprocess1.' + filename.split('.')[-1]
        print(output_files)
        cv.imwrite(os.path.join(pathout, output_files), src)
        
        
    return [os.path.join(pathout, output_files)]



def main():
    filelist= ['test_left.jpeg', 'test_right.jpeg']
    outpath = os.path.join(os.path.dirname(__file__), "sample_input/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':

    filelist= ['test_left.jpeg', 'test_right.jpeg']
    task(filelist, '/home/zxc/Desktop/imgptest/sample_input', '/home/zxc/Desktop/imgptest/generated_files')


