import os
import time
import shutil
import math
import random

def task(filename,pathin,pathout):
	outfile = []
	if type(filename) is list:
		pass
	else:
		filename = [filename]
	for f in filename:
		print(f)
		appname = f.split('-')[0]
		print(appname)
		print(pathin)
		print(pathout)
		file_in = os.path.join(pathin,f)
		file_out = os.path.join(pathout,f)
		cmd = 'cp %s %s'%(file_in,file_out)
		os.system(cmd)
		outfile.append(file_out)
	return outfile

def main():
	filelist = ['dummyapp1-1botnet.ipsum','dummyapp2-1botnet.ipsum']
	inpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
	outpath = os.path.join(os.path.dirname(__file__), 'generated_files/')
	outfile = task(filelist, inpath, outpath)
	return outfile


