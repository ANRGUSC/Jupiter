__author__ = "Jiatong Wang, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"

import time, os

def re_exe(cmd, inc = 60):
	"""Perform the command every interval
    
    Args:
        - cmd (str): command name
        - inc (int, optional): interval time
    """

    while True:
        os.system(cmd)
        time.sleep(inc)

def main():
	"""
		Update resource information per minute by performing resource profiling process every minute
	"""
	re_exe("python3 /resource_profiling/insert_to_container.py /resource_profiling/ip_path", 60)

if __name__ == '__main__':
	main()
