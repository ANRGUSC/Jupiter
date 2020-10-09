import os
import time
import sys

LOOP_RANGE = 20000000
TASK_NAME = "task3"
NUM_BLOCK = 3000

def task(input_files, pathin, pathout):


    filelist=[]
    filelist.append(input_files)

    count = 0
    for i in range(LOOP_RANGE):
        count = count + 1
        count = count - 1

    output_files = input_files[0].split('_')[0] + "_" + TASK_NAME
    # output_files = input_files.split('_')[0] + "_" + TASK_NAME
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


