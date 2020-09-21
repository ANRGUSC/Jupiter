"""
	This Function is used to keep the pods alive even after all process ends
"""
__author__ = "Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import time
def main():
	while 1:
	    time.sleep(120)

if __name__ == '__main__':
    main()