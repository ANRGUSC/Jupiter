import os
import time
import sys

'''
python3 {THIS_SCRIPT} {INPUT_FILE_NUMBER} {TIME_INTERVAL}
e.g. python3 generate_input.py 10 5 > stdout 2>&1 &
'''

def main():
    input_id = 0
    while(input_id < int(sys.argv[1])):
        cmd = "cat 'input' > input_%s" % str(input_id)
        os.system(cmd)
        input_id += 1
        time.sleep(int(sys.argv[2]))
        
if __name__ == '__main__':

    main()
