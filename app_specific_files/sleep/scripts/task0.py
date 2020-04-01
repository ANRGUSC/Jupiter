import os
import time
import sys

def task(input_files, pathin, pathout):


    filelist=[]
    filelist.append(input_files)

    # input_files is a string, not a lost
    time.sleep(10)
    cmd = "dd bs=1024 count=8192 </dev/urandom >%s/%s_%s" % (pathout, input_files, sys.argv[0].split('.')[0])
    os.system(cmd)
    return [os.path.join(pathout,input_files[0] + sys.argv[0])]



def main():
    filelist= 'input0'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile
'''
if __name__ == '__main__':

    #Suppose the file structure is erick/detection_app/camera1_input/camera1_20190222.jpeg
    filelist= 'input0'
    task(filelist, '/home/erick/detection_app/camera1_input', '/home/erick/detection_app')
'''

