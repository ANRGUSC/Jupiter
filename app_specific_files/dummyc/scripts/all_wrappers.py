
import ctypes 
import os
import time
import shutil
import math
import random
import subprocess

def task(filename,pathin,pathout):
     tasks = {"task0.c" : 4, "task1.c" : 1, "task2.c" : 3, "task3.c" : 3, "task4.c" : 1, "task5.c" : 1, "task6.c" : 1 }
     #tasks = ['task0.c', 'task1.c', 'task2.c', 'tak3.c', 'task4.c]
     final = []
     for k in tasks:
        v = "libtest" + k.split('.')[0] + ".so"
        subprocess.call(["gcc","-o",v,"-shared","-fPIC",k])
        cmd = "./" + v
        lib = ctypes.CDLL(cmd)
        string_buffers = [ctypes.create_string_buffer(128) for i in range(tasks[k])]
        
        pointers = (ctypes.c_char_p*(tasks[k]))(*map(ctypes.addressof, string_buffers))
        lib.main(pointers)
        results = [s.value for s in string_buffers]
        r = [i.decode('utf-8') for i in results]
        final.append(r)
     return final

def main():
    filelist = '1botnet.ipsum'
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    print(outfile)
    return outfile
    
    
if __name__ == "__main__":
    main()
