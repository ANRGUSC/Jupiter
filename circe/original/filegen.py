import os
import time
import sys

'''
python3 {THIS_SCRIPT} {INPUT_FILE_NUMBER} {TIME_INTERVAL}
e.g. python3 filegen.py 10 1 &  // generate 10 files (input1 ~ input9), with interval of 1 sec
'''

def main():
    input_id = 1
    while(input_id < int(sys.argv[1])):
        cmd = "touch input/input%s" % str(input_id)
        os.system(cmd)
        input_id += 1
        time.sleep(int(sys.argv[2]))
        
if __name__ == '__main__':

    main()
