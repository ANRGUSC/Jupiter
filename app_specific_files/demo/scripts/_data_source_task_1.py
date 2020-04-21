# Bunch of import statements
import os
import shutil
import random
"""
Task for data input node
"""
current_idx = 0

def find_next_file(local_folder):
    global current_idx
    list_files = os.listdir(local_folder)
    current_idx += 1
    #current_idx = random.randint(0 , len(list_files)-1)
    if current_idx >= len(list_files):
        current_idx = current_idx % len(list_files)
    return list_files[current_idx]

def task(file_, pathin, pathout):
    out_list = []
    print("received the file with name: ", file_)
    class_name = "fireengine" # "schoolbus"
    local_folder = "./datasources/" + class_name 
    file_name = find_next_file(local_folder)
    source = os.path.join(local_folder, file_name)
    destination = os.path.join(pathout, "outds1prefix_" + file_name) #"outds2prefix_"
    try: 
        out_list.append(shutil.copyfile(source, destination))
    except: 
        print("ERROR while copying file in data_source_task.py")
    return out_list 
	
if __name__ == "__main__":
    #filelist = ['n03345487_1002.JPEG']
    file_ = 'random.txt'
    #for f in filelist:
    task(file_, "./outdummy" , "./to_master/")
