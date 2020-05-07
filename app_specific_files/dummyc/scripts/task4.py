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
     filename= "task4.c"
     subprocess.call(["gcc","-o","task4.so","-shared","-fPIC","task4.c"])
     task4_lib = cdll.LoadLibrary("./task4.so")
     s = task4_lib.main
     s.restype = c_char_p
     return s()

def main():
	filelist = '1botnet.ipsum'
	outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
	outfile = task(filelist, outpath, outpath)
	return outfile
    
if __name__ == "__main__":
    main()
