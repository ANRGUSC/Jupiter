# Bunch of import statements
import os
import shutil
from pathlib import Path
from os import listdir

taskname = Path(__file__).stem
classnum = taskname.split('storeclass')[1]
"""
Task for node that stores classified images belonding to it's assigned class.
"""
def task(file_, pathin, pathout):
    file_ = [file_] if isinstance(file_, str) else file_
    out_list = []
    for i, f in enumerate(file_):
        source = os.path.join(pathin, f) 
        # file_split = file_.split("prefix_")[1]
        destination = os.path.join(pathout, "storeclass"+classnum+"_" + f)
        print(source)
        print(destination)
        try: 
            shutil.copyfile(source, destination)
            out_list.append(destination)
        except: 
            print("ERROR while copying file in store_class_task.py")
    return out_list

def main():
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    # filelist = (f for f in listdir(outpath) if f.startswith('resnet'))
    filelist = [f for f in listdir(outpath) if taskname in f]
    outfile = task(filelist, outpath, outpath)
    return outfile
	
