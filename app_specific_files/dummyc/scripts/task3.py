
import ctypes 
import os
import time
import shutil
import math
import random
import subprocess

def task(filename,pathin,pathout):
     filename= "task3.c"
     subprocess.call(["gcc","-o","libtest.so","-shared","-fPIC","task3.c"])
    


     lib = ctypes.CDLL("./libtest.so")
     string_buffers = [ctypes.create_string_buffer(128) for i in range(3)]
     pointers = (ctypes.c_char_p*3)(*map(ctypes.addressof, string_buffers))
     lib.main(pointers)
     results = [s.value for s in string_buffers]
     r = [i.decode('utf-8') for i in results]
     return(r)

def main():
	filelist = '1botnet.ipsum'
	outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
	outfile = task(filelist, outpath, outpath)
	return outfile
    
if __name__ == "__main__":
    main()
