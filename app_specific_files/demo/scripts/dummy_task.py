import os
import random
import time
"""
send a file to data sources at chosen interval (1 second for now)
dummy 2 hybrid ds1 ds2
"""
def task(f, pathin, pathout):
    print("dummy task: received input file with name: ", f)
    interval = 1000
    num_classes = 2 # the total number of different classes in the DAG.
    class_idx = random.randint(0, num_classes - 1)
    with open("./outdummy_"+ str(int(time.time())) + ".txt", "w") as out_file:
        out_file.write(str(class_idx)) 
    out_list = [out_file]
    return out_list

if __name__ == "__main__":
    file_ = "inp_dummy.txt"
    pathin = ""
    pathout = ""
    task(file_, pathin, pathout)
