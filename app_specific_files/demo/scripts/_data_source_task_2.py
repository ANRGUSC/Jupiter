# Bunch of import statements
import os
import shutil
"""
Task for data input node
"""
def task(file_, pathin, pathout):
    out_list = []
    source = os.path.join(pathin, file_) 
    destination = os.path.join(pathout, "outds2prefix_" + file_)
    try: 
        out_list.append(shutil.copyfile(source, destination))
    except: 
        print("ERROR while copying file in data_source_task.py")
    return out_list 
	
if __name__ == "__main__":
    filelist = ['n04146614_10015.JPEG']
    class_name = "schoolbus"
    for f in  filelist:
        task(f, "./datasources/" + class_name + "/", "./to_master/")
