import os
import time
import sys

EXEC_TIME = 40
TASK_NAME = "task1"
NUM_BLOCK = 8192

def task(input_files, pathin, pathout):


    filelist=[]
    filelist.append(input_files)

    start_time = time.time()
    count = 0
    while(1):
        count = count + 1
        count = count - 1
        cur_time = time.time()
        if cur_time - start_time > EXEC_TIME:
            break
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


