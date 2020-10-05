import os
import time
import sys

'''
e.g. python3 filegen.py 90 1 &
'''

def main():
    input_id = 1
    while(input_id < int(sys.argv[1])):
        cmdl = "cp sample_input/test_data/input%s_left.jpeg /input" % str(input_id)
        os.system(cmdl)
        time.sleep(float(sys.argv[2]))
        cmdr = "cp sample_input/test_data/input%s_right.jpeg /input" % str(input_id)
        os.system(cmdr)
        input_id += 1
        time.sleep(float(sys.argv[2]))
        
if __name__ == '__main__':

    main()
