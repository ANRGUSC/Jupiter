import os
import time
import sys

EXEC_TIME = 0.16
TASK_NAME = "task0"
NUM_BLOCK = 4000

def task(input_files, pathin, pathout):


    filelist=[]
    filelist.append(input_files)

    time.sleep(EXEC_TIME)
    output_files = input_files.split('_')[0] + "_" + TASK_NAME
    cmd = "dd bs=1024 count=%d </dev/urandom >%s/%s" % (NUM_BLOCK, pathout, output_files)
    os.system(cmd)
    return [os.path.join(pathout, output_files)]

def main():
    filelist= 'input0'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':

    filelist= 'input0'
    task(filelist, '../sample_input', '.')


