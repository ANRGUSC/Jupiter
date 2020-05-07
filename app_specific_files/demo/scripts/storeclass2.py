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
    #filelist = ['resnet5_storeclass2_master_resnet5_n04146614_16038.JPEG']
    filelist = ['resnet0_storeclass2_master_resnet0_n04146614_1.JPEG','resnet0_storeclass2_master_resnet0_n04146614_25.JPEG','resnet0_storeclass2_master_resnet0_n04146614_27.JPEG',
       'resnet0_storeclass2_master_resnet0_n04146614_30.JPEG','resnet0_storeclass2_master_resnet0_n04146614_36.JPEG',
       'resnet1_storeclass2_master_resnet1_n04146614_39.JPEG',
       'resnet1_storeclass2_master_resnet1_n04146614_53.JPEG','resnet1_storeclass2_master_resnet1_n04146614_69.JPEG','resnet1_storeclass2_master_resnet1_n04146614_79.JPEG',
       'resnet1_storeclass2_master_resnet1_n04146614_84.JPEG',
       'resnet2_storeclass2_master_resnet2_n04146614_152.JPEG','resnet2_storeclass2_master_resnet2_n04146614_158.JPEG','resnet2_storeclass2_master_resnet2_n04146614_186.JPEG','resnet2_storeclass2_master_resnet2_n04146614_187.JPEG',
       'resnet2_storeclass2_master_resnet2_n04146614_199.JPEG',
       'resnet3_storeclass2_master_resnet3_n04146614_209.JPEG','resnet3_storeclass2_master_resnet3_n04146614_231.JPEG',
       'resnet3_storeclass2_master_resnet3_n04146614_232.JPEG','resnet3_storeclass2_master_resnet3_n04146614_237.JPEG','resnet3_storeclass2_master_resnet3_n04146614_245.JPEG',
       'resnet4_storeclass2_master_resnet4_n04146614_263.JPEG','resnet4_storeclass2_master_resnet4_n04146614_284.JPEG','resnet4_storeclass2_master_resnet4_n04146614_295.JPEG',
       'resnet4_storeclass2_master_resnet4_n04146614_309.JPEG','resnet4_storeclass2_master_resnet4_n04146614_312.JPEG',
       'resnet5_storeclass2_master_resnet5_n04146614_16038.JPEG','resnet5_storeclass2_master_resnet5_n04146614_318.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
	