# Bunch of import statements
import os
import shutil
"""
Task for node that stores classified images belonding to it's assigned class.
"""
def task(file_, pathin, pathout):
    out_list = []
    for i, f in enumerate(file_):
        source = os.path.join(pathin, f) 
        # file_split = file_.split("prefix_")[1]
        destination = os.path.join(pathout, "outstore1_" + f)
        print(source)
        print(destination)
        try: 
            shutil.copyfile(source, destination)
            out_list.append(destination)
        except: 
            print("ERROR while copying file in store_class_task.py")
    return out_list 

def main():
    filelist = ['class1_n03345487_1002.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
	
# if __name__ == "__main__":
#     filelist = ['class1_prefix_n03345487_1002.JPEG']
#     class_num = 1    
#     #for f in filelist:
#     task(f, "./classified_images/", "./store_class_"+ str(class_num) + "/")
