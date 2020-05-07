from ctypes import cdll
from ctypes import c_char_p
import ctypes 
import os
import time
import shutil
import math
import random
import subprocess

def task(filename,pathin,pathout):
     filename= "task2.c"
     subprocess.call(["gcc","-o","task2.so","-shared","-fPIC","task2.c"])
     task2_lib = cdll.LoadLibrary("./task2.so")
     s = task2_lib.main
     s.restype = c_char_p
     return s()

def main():
	filelist = '1botnet.ipsum'
	outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
	outfile = task(filelist, outpath, outpath)
	return outfile
    
if __name__ == "__main__":
    main()
