import os
import time
import shutil
import math
import random
import subprocess

def task(filename,pathin,pathout):
     filename= "task4.c"
     subprocess.call(["gcc",filename])
     subprocess.call("./a.out")
        

def main():
	filelist = '1botnet.ipsum'
	outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
	outfile = task(filelist, outpath, outpath)
	return outfile
    
if __name__ == "__main__":
    main()
