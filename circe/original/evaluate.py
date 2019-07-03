#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    .. note:: This script is used entirely for evaluation purpose.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"


import shutil
import os
import random
import time
import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import PatternMatchingEventHandler


def evaluate_random():
    """
    Copy files from folder ``sample_input`` to folder ``input`` at random intervals for evaluation 
    
    """
    file_count = len(os.listdir("sample_input/")) 
    interval = 120
    for i in range(1,file_count+1):
        n = random.randint(1,interval)
        count = 0
        while count<n:
            count = count+1
            time.sleep(1)
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)

def evaluate_interval(interval):
    """
    Copy files from folder ``sample_input`` to folder ``input`` at regular intervals for evaluation 

    Args:
        interval (int): interval time to inject the sample input file
    
    """
    file_count = len(os.listdir("sample_input/")) 
    for i in range(1,file_count+1):
        count = 0
        while count<interval:
            count = count+1
            time.sleep(1)
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)

def evaluate_sequential():
    """
    Copy files from folder ``sample_input`` to folder ``input`` one after another for evaluation 
    
    """
    file_count = len(os.listdir("sample_input/"))
    file_count_out = len(os.listdir("output/"))
    print('---- Generate random input files')
    # file_count = 2
    for i in range(1,file_count+1):
        src = "sample_input/%dbotnet.ipsum"%i
        dest = "input/%dbotnet.ipsum"%i
        print('---- Generate random input files')
        shutil.copyfile(src,dest)
        count = 0
        while 1:
            time.sleep(5)
            file_count_out = len(os.listdir("output/"))
            if file_count_out ==  i:
                time.sleep(30)
                break


    print('---- Finish generating sequential input files')

def evaluate_test():
    file_count = len(os.listdir("sample_input/"))
    print(file_count)
    file_count_out = len(os.listdir("output/"))
    print(file_count_out)
    for filepath in glob.iglob('sample_input/*.ipsum'):
        print(filepath)
        filename = filepath.split('/')[1]
        dest = "input/"+filename
        print('---- Generate random input files')
        shutil.copyfile(filepath,dest)
        count = 0
        while 1:
            time.sleep(5)
            file_count_out = len(os.listdir("output/"))
            if file_count_out ==  file_count:
                time.sleep(30)
                break

def evaluate_combine(num_apps,num_samples):
    file_count = len(os.listdir("sample_input/"))
    print(file_count)  
    file_count_out = len(os.listdir("output/")) 
    print(file_count_out)
    count = 0
    for i in range(1,num_samples+1):
        print('---- Generate random input files')
        for j in range(1,num_apps+1):
            filein = 'sample_input/dummyapp%d-%dbotnet.ipsum'%(j,i)
            fileout ='input/dummyapp%d-%dbotnet.ipsum'%(j,i)
            shutil.copyfile(filein,fileout)
        count = count+num_apps
        
        while 1:
            time.sleep(5)
            file_count_out = len(os.listdir("output/"))
            print('-----Checking')
            print(file_count_out)
            print(count)
            if file_count_out ==  count:
                print('Finishing all the current samples')
                break
        print('Continue to generate more random input files')

def evaluate_combine_app(num_apps,num_samples):
    print('---- Generate random input files')
    for i in range(1,num_apps+1):
        filein = 'sample_input/dummyapp%d-1botnet.ipsum'%(i)
        fileout ='input/dummyapp%d-1botnet.ipsum'%(i)
        shutil.copyfile(filein,fileout)   
    output_folder = 'output/'
    outfile = set()
    while 1:
        time.sleep(10)
        print('Generate more random input files')
        print('------')
        for (dirpath, dirnames, filenames) in os.walk(output_folder):
            for filename in filenames:
                input_file = filename.split('_')[0] 
                # print(input_file)
                if input_file not in outfile:
                    # print(input_file)
                    appname = input_file.split('-')[0]
                    # print(appname)
                    # print(input_file.split('-')[1])
                    curfile = input_file.split('-')[1].split('botnet')[0]
                    # print(curfile)
                    curnum = int(curfile)+1
                    if curnum >num_samples: continue
                    
                    newfile = 'sample_input/'+appname+'-'+str(curnum)+'botnet.ipsum'
                    print(newfile)
                    fileout ='input/'+appname+'-'+str(curnum)+'botnet.ipsum'
                    # print(fileout)
                    shutil.copyfile(newfile,fileout)
                    outfile.add(input_file)
        print('------')
        print(outfile)


class MyHandler(PatternMatchingEventHandler):
    """
    Handling the event when there is a new file generated in ``OUTPUT`` folder
    """

    def process(self, event):
        """
        Log the time the file is created and calculate the execution time whenever there is an event.
        
        Args:
            event: event to be watched for the ``OUTPUT`` folder
        """

        global start_times
        global end_times
        global exec_times
        global count

        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        if event.event_type == 'created':
            # print('***************************************************')
            print("Received file as output in evaluation - %s." % event.src_path)  
            filename = os.path.split(event.src_path)[-1]
            appname = filename.split('-')[0]
            print(appname)
            curfile = filename.split('-')[1].split('botnet')[0]
            print(curfile)
            curnum = int(curfile)+1
            if curnum < num_samples: 
                newfile = 'sample_input/'+appname+'-'+str(curnum)+'botnet.ipsum'
                print(newfile)
                fileout ='input/'+appname+'-'+str(curnum)+'botnet.ipsum'
                # print(fileout)
                shutil.copyfile(newfile,fileout)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

        
        

if __name__ == '__main__':
    #evaluate_random()
    time.sleep(60)
    print('Start copying sample files for evaluation')

    evaluate_sequential()

    #evaluate_test()
    

    # global num_apps, num_samples
    # num_apps = 100
    # num_samples = 10
    # print('---- Generate random input files')
    # for i in range(1,num_apps+1):
    #     filein = 'sample_input/dummyapp%d-1botnet.ipsum'%(i)
    #     fileout ='input/dummyapp%d-1botnet.ipsum'%(i)
    #     shutil.copyfile(filein,fileout) 
    
    # print("Starting the output monitoring system:")
    # observer = Observer()
    # observer.schedule(MyHandler(), path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'output/'))
    # observer.start()

    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     observer.stop()

    # observer.join()