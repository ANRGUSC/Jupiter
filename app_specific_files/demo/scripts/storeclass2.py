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
    filelist = ['resnet5_storeclass2_master_resnet5_n04146614_16038.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
	