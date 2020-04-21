# Bunch of import statements
import os
import shutil
"""
Task for node that stores classified images belonding to it's assigned class.
"""
def task(file_, pathin, pathout):
    out_list = []
    source = os.path.join(pathin, file_) 
    file_split = file_.split("prefix_")[1]
    destination = os.path.join(pathout, "outstore1prefix_" + file_split)
    try: 
        out_list.append(shutil.copyfile(source, destination))
    except: 
        print("ERROR while copying file in store_class_task.py")
    return out_list 
	
if __name__ == "__main__":
    filelist = ['class1_prefix_n03345487_1002.JPEG']
    class_num = 1    
    #for f in filelist:
    task(f, "./classified_images/", "./store_class_"+ str(class_num) + "/")
