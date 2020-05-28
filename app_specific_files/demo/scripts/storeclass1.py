# Bunch of import statements
import os
import shutil
"""
Task for node that stores classified images belonding to it's assigned class.
"""
def task(file_, pathin, pathout):
    file_ = [file_] if isinstance(file_, str) else file_
    out_list = []
    for i, f in enumerate(file_):
        source = os.path.join(pathin, f) 
        # file_split = file_.split("prefix_")[1]
        destination = os.path.join(pathout, "storeclass1_" + f)
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
    filelist = ['resnet0_storeclass1_master_resnet0_n03345487_10_jobid_0.JPEG',
    'resnet1_storeclass1_master_resnet1_n03345487_108_jobid_0.JPEG',
    'resnet2_storeclass1_master_resnet2_n03345487_133_jobid_0.JPEG',
    'resnet3_storeclass1_master_resnet3_n03345487_135_jobid_0.JPEG',
    'resnet4_storeclass1_master_resnet4_n03345487_136_jobid_0.JPEG',
    'resnet5_storeclass1_master_resnet5_n03345487_144_jobid_0.JPEG','resnet5_storeclass1_master_resnet5_n03345487_163_jobid_0.JPEG','resnet5_storeclass1_master_resnet5_n03345487_192_jobid_0.JPEG',
       'resnet5_storeclass1_master_resnet5_n03345487_205_jobid_0.JPEG',
       'resnet6_storeclass1_master_resnet6_n03345487_18_jobid_0.JPEG','resnet6_storeclass1_master_resnet6_n03345487_206_jobid_0.JPEG','resnet6_storeclass1_master_resnet6_n03345487_208_jobid_0.JPEG','resnet6_storeclass1_master_resnet6_n03345487_209_jobid_0.JPEG','resnet6_storeclass1_master_resnet6_n03345487_210_jobid_0.JPEG','resnet6_storeclass1_master_resnet6_n03345487_241_jobid_0.JPEG',
       'resnet7_storeclass1_master_resnet7_n03345487_40_jobid_0.JPEG','resnet7_storeclass1_master_resnet7_n03345487_243_jobid_0.JPEG','resnet7_storeclass1_master_resnet7_n03345487_245_jobid_0.JPEG','resnet7_storeclass1_master_resnet7_n03345487_267_jobid_0.JPEG',
       'resnet7_storeclass1_master_resnet7_n03345487_279_jobid_0.JPEG','resnet7_storeclass1_master_resnet7_n03345487_282_jobid_0.JPEG',
       'resnet8_storeclass1_master_resnet8_n03345487_78_jobid_0.JPEG','resnet8_storeclass1_master_resnet8_n03345487_284_jobid_0.JPEG',
       'resnet8_storeclass1_master_resnet8_n03345487_311_jobid_0.JPEG','resnet8_storeclass1_master_resnet8_n03345487_317_jobid_0.JPEG','resnet8_storeclass1_master_resnet8_n03345487_328_jobid_0.JPEG',
       'resnet8_storeclass1_master_resnet8_n03345487_334_jobid_0.JPEG',
       'resnet0_storeclass1_master_resnet0_n03345487_351_jobid_0.JPEG',
       'resnet1_storeclass1_master_resnet1_n03345487_360_jobid_0.JPEG',
       'resnet2_storeclass1_master_resnet2_n03345487_386_jobid_0.JPEG',
       'resnet3_storeclass1_master_resnet3_n03345487_410_jobid_0.JPEG',
       'resnet4_storeclass1_master_resnet4_n03345487_417_jobid_0.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
	
