import os
import time
import shutil
import math
import random
from multiprocessing import Pool
from multiprocessing import cpu_count

def task(filename,pathin,pathout):
	execution_time = 2.4
	execution_time
	count = cpu_count()
	cmd = 'stress --cpu %d --timeout %ds &' %(count,execution_time)
	os.system(cmd)
	task_name = os.path.basename(__file__).split('.')[0]
	if isinstance(filename, list):
		output1_list = [file.split('.')[0] +'_'+task_name+'.txt' for file in filename]
		input_file = filename[0].split('_')[0]
	elif not isinstance(filename, list):
		output1_list=[filename.split('.')[0] +'_'+task_name+'.txt']
		input_file = filename.split('_')[0]
	output1=set(output1_list)
	output_fname=[f.split('.')[0].split('_')[-1] for f in output1]
	output_name='_'.join(output_fname)
	output_name=input_file+'_'+output_name
	f = open('/centralized_scheduler/communication.txt', 'r')
	total_info = f.read().splitlines()
	f.close()
	comm = dict()
	for line in total_info:
		src = line.strip().split(' ')[0]
		dest_info = line.strip().split(' ')[1:]
		if len(dest_info)>0:
			comm[src] = dest_info
	if not os.path.isdir(pathout):
		os.makedirs(pathout, exist_ok=True)
	output_path=[]
	if task_name in comm.keys():
		dest=[x.split('#')[0] for x in comm[task_name]]
		comm_data=[str(math.ceil(float(x.split('#')[1]))) for x in comm[task_name]]
		output_list=[]
		file_size=[]
		for idx,neighbor in enumerate(dest):
			new_file=output_name+'_'+neighbor
			output_list.append(new_file)
			file_size.append(comm_data[idx])
			new_path=os.path.join(pathout,new_file) 
			output_path.append(new_path)
			bash_script='/centralized_scheduler/generate_random_files.sh'+' '+new_path+' '+comm_data[idx]
			os.system(bash_script)
	elif task_name not in comm.keys():
		new_file=output_name+'_'+task_name
		new_path=os.path.join(pathout,new_file) 
		output_path.append(new_path)
		file_size=str(random.randint(1,20))
		bash_script='/centralized_scheduler/generate_random_files.sh'+' '+new_path+' '+file_size
		os.system(bash_script)

	return output_path

def main():
	filelist = '1botnet.ipsum'
	outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
	outfile = task(filelist, outpath, outpath)
	return outfile
