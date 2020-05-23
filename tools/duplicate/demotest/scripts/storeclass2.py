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
    # filelist = ['resnet2_storeclass1_master_resnet2_n03345487_133.JPEG']
    # filelist = ['resnet0_storeclass1_master_resnet0_n03345487_10.JPEG',
    # 'resnet1_storeclass1_master_resnet1_n03345487_108.JPEG',
    # 'resnet2_storeclass1_master_resnet2_n03345487_133.JPEG',
    # 'resnet3_storeclass1_master_resnet3_n03345487_135.JPEG',
    # 'resnet4_storeclass1_master_resnet4_n03345487_136.JPEG',
    # 'resnet5_storeclass1_master_resnet5_n03345487_144.JPEG','resnet5_storeclass1_master_resnet5_n03345487_163.JPEG','resnet5_storeclass1_master_resnet5_n03345487_192.JPEG',
    #    'resnet5_storeclass1_master_resnet5_n03345487_205.JPEG',
    #    'resnet6_storeclass1_master_resnet6_n03345487_18.JPEG','resnet6_storeclass1_master_resnet6_n03345487_206.JPEG','resnet6_storeclass1_master_resnet6_n03345487_208.JPEG','resnet6_storeclass1_master_resnet6_n03345487_209.JPEG','resnet6_storeclass1_master_resnet6_n03345487_210.JPEG','resnet6_storeclass1_master_resnet6_n03345487_241.JPEG',
    #    'resnet7_storeclass1_master_resnet7_n03345487_40.JPEG','resnet7_storeclass1_master_resnet7_n03345487_243.JPEG','resnet7_storeclass1_master_resnet7_n03345487_245.JPEG','resnet7_storeclass1_master_resnet7_n03345487_267.JPEG',
    #    'resnet7_storeclass1_master_resnet7_n03345487_279.JPEG','resnet7_storeclass1_master_resnet7_n03345487_282.JPEG',
    #    'resnet8_storeclass1_master_resnet8_n03345487_78.JPEG','resnet8_storeclass1_master_resnet8_n03345487_284.JPEG',
    #    'resnet8_storeclass1_master_resnet8_n03345487_311.JPEG','resnet8_storeclass1_master_resnet8_n03345487_317.JPEG','resnet8_storeclass1_master_resnet8_n03345487_328.JPEG',
    #    'resnet8_storeclass1_master_resnet8_n03345487_334.JPEG',
    #    'resnet0_storeclass1_master_resnet0_n03345487_351.JPEG',
    #    'resnet1_storeclass1_master_resnet1_n03345487_360.JPEG',
    #    'resnet2_storeclass1_master_resnet2_n03345487_386.JPEG',
    #    'resnet3_storeclass1_master_resnet3_n03345487_410.JPEG',
    #    'resnet4_storeclass1_master_resnet4_n03345487_417.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    # filelist = (f for f in listdir(outpath) if f.startswith('resnet'))
    filelist = [f for f in listdir(outpath) if taskname in f]
    outfile = task(filelist, outpath, outpath)
    return outfile
	
