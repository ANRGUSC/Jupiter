import os
import time

def task(input_files, pathin, pathout):


    filelist=[]
    filelist.append(input_files)

    time.sleep(20)
    file_gen = "dd bs=1024 count=8192 </dev/urandom >%s/output_task0_file0" % pathout
    os.system(cmd)
    return [os.path.join(pathout,'output_task0_file0')]



def main():
    filelist= 'input_0'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile
    
'''
if __name__ == '__main__':

    #Suppose the file structure is erick/detection_app/camera1_input/camera1_20190222.jpeg
    filelist= 'input_0'
    task(filelist, '/home/erick/detection_app/camera1_input', '/home/erick/detection_app')
'''

