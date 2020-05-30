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
        destination = os.path.join(pathout, "storeclass2_" + f)
        print(source)
        print(destination)
        try: 
            shutil.copyfile(source, destination)
            out_list.append(destination)
        except: 
            print("ERROR while copying file in store_class_task.py")
    return out_list



def main():
    #filelist = ['resnet5_storeclass2_master_resnet5_n04146614_16038_jobid_0.JPEG']
    filelist = ['resnet0_storeclass2_master_resnet0_n04146614_1_jobid_0.JPEG','resnet0_storeclass2_master_resnet0_n04146614_25_jobid_0.JPEG','resnet0_storeclass2_master_resnet0_n04146614_27_jobid_0.JPEG',
       'resnet0_storeclass2_master_resnet0_n04146614_30_jobid_0.JPEG','resnet0_storeclass2_master_resnet0_n04146614_36_jobid_0.JPEG',
       'resnet1_storeclass2_master_resnet1_n04146614_39_jobid_0.JPEG',
       'resnet1_storeclass2_master_resnet1_n04146614_53_jobid_0.JPEG','resnet1_storeclass2_master_resnet1_n04146614_69_jobid_0.JPEG','resnet1_storeclass2_master_resnet1_n04146614_79_jobid_0.JPEG',
       'resnet1_storeclass2_master_resnet1_n04146614_84_jobid_0.JPEG',
       'resnet2_storeclass2_master_resnet2_n04146614_152_jobid_0.JPEG','resnet2_storeclass2_master_resnet2_n04146614_158_jobid_0.JPEG','resnet2_storeclass2_master_resnet2_n04146614_186_jobid_0.JPEG','resnet2_storeclass2_master_resnet2_n04146614_187_jobid_0.JPEG',
       'resnet2_storeclass2_master_resnet2_n04146614_199_jobid_0.JPEG',
       'resnet3_storeclass2_master_resnet3_n04146614_209_jobid_0.JPEG','resnet3_storeclass2_master_resnet3_n04146614_231_jobid_0.JPEG',
       'resnet3_storeclass2_master_resnet3_n04146614_232_jobid_0.JPEG','resnet3_storeclass2_master_resnet3_n04146614_237_jobid_0.JPEG','resnet3_storeclass2_master_resnet3_n04146614_245_jobid_0.JPEG',
       'resnet4_storeclass2_master_resnet4_n04146614_263_jobid_0.JPEG','resnet4_storeclass2_master_resnet4_n04146614_284_jobid_0.JPEG','resnet4_storeclass2_master_resnet4_n04146614_295_jobid_0.JPEG',
       'resnet4_storeclass2_master_resnet4_n04146614_309_jobid_0.JPEG','resnet4_storeclass2_master_resnet4_n04146614_312_jobid_0.JPEG',
       'resnet5_storeclass2_master_resnet5_n04146614_16038_jobid_0.JPEG','resnet5_storeclass2_master_resnet5_n04146614_318_jobid_0.JPEG',
       'resnet5_storeclass2_master_resnet5_n04146614_330_jobid_0.JPEG',
       'resnet6_storeclass2_master_resnet6_n04146614_363_jobid_0.JPEG',
       'resnet7_storeclass2_master_resnet7_n04146614_377_jobid_0.JPEG',
       'resnet8_storeclass2_master_resnet8_n04146614_387_jobid_0.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
	
