

import os
import time
import shutil
import math
import random
import subprocess

def generate_scripts(dag,config_path,script_path,app_path,sample_path):
    

    print('------ Read input parameters from DAG  -------------')
    sorted_list = sorted(dag.nodes(data=True), key=lambda x: x[0], reverse=False)
    f = open(config_path, 'r')
    total_line = f.readlines()
    del total_line[0]
    f.close()


    for i in range(len(total_line)):
        tmp = total_line[i].split(' ')
        filename = tmp[0] + ".c"
        num = int(tmp[1])
        file_path = script_path + filename

        f = open(file_path, 'w')
        f.write("#include<stdio.h>\n")
        f.write("#include<stdlib.h>\n")
        f.write("#include<string.h>\n")
        f.write("#include<math.h>\n")
        f.write("#include<time.h>\n")
        f.write("#include<sys/stat.h>\n")
        f.write("#include<sys/types.h>\n")
        f.write("#define PATH_MAX 128\\n")
        f.write("#include<libgen.h>\n")

        f.write("int tot=i;\n")
        f.write("char filename[128][128];\n")
        f.write("char file_path[128][128];\n")
        f.write("int execution_time;\n")
        f.write("char* task_name;\n")
        f.write("char output1_list[128];\n")
        f.write("char input_file[128];\n")
		f.write("char bash_script[128];\n")
        f.write("FILE* f;\n")
        f.write("char comm [128][128];\n")
        f.write("char *src[128][20];\n")
        f.write("char* new_path[128];\n")
        f.write("int loop_var;\n")
        f.write("char* ptr;\n")

        f.write("\n")
        f.write("char* task(filename,pathin,pathout)\n")
        f.write("{ \n")
        f.write("\texecution_time = rand() % 10;\n")
        f.write('\tprintf("%d",execution_time);\n')
        f.write("\ttime_t timeout;\n")
        f.write("\ttimeout = time(&timeout) + execution_time;\n")

        f.write("\twhile (time(&timeout) < timeout)\n")
        f.write("{ \n")
        f.write("\t\t1+1 ;\n")
        f.write("} \n")

        f.write("\tchar *path = '__FILE__';\n")
        f.write("\tchar *path_cpy = strdup(path);\n")
        f.write("\ttask_name=basename(path_cpy);\n")
        f.write('\tprintf("-------------------------");\n')
        f.write('\tprintf("%s",task_name);\n')
        f.write('\tprintf("%s",filename);\n')
        #f.write("\tprintf(pathin)\n")
        #f.write("\tprint(pathout)\n")
        f.write('\tprintf("-------------------------" );\n')
        f.write("\t\tstrcpy(output1_list,&filename);\n")
        f.write('\t\tstrcat(output1_list,"_"");\n')
        f.write("\t\tstrcat(output1_list,&task_name[0]);\n")
        f.write('\t\tstrcat(output1_list,".txt") ;\n')
        f.write("\t\tstrcpy(input_file, &filename);\n")
        f.write('\tprintf("%s",output1_list);\n')
        f.write('\tprintf("%s",input_file);\n')

        f.write('\t\tchar output_name[128]=strcat(input_file,"_");\n')
        f.write("\t\tstrcat(output_name,output_name);")
        f.write('\tprint("%s",output_name);\n')
        f.write('\tprintf("---------------------------");\n')

        f.write("\tchar actualpath [PATH_MAX+1];\n")
        f.write('\tchar *file_comm [PATH_MAX+1]= "communication.txt";\n')
        f.write("\tchar *ptr;;\n")
        f.write("\tptr=realpath(file_comm,actualpath);\n")
        f.write('\tprintf("%s",ptr);\n')

        f.write("\tFILE* f;\n")
        f.write('\tfopen(/centralized_scheduler/communication.txt, "r" );\n')
        f.write("\tfclose(f);\n")

        f.write("\tchar temp_comm [128][128];\n")
        f.write("\tchar comm [128][128];\n")
        f.write('\tmemset(temp_comm, "\0", sizeof(temp_comm));\n')
        f.write("\tmemset(comm, '\0', sizeof(comm));;\n")
        f.write("\tchar line_read [128];\n")
        f.write("\tmemset(line_read, '\0', sizeof(line_read));\n")
        f.write("\tint k = 0;\n")
        f.write("\twhile( fgets( line_read, sizeof(line_read), f ) != NULL )\n")
        f.write("{ \n")
        f.write("\tstrcpy(temp_comm[k], line_read);\n")
        f.write("\tk++;\n")
        f.write("} \n")
        f.write("\tint sum_k = k;\n")
        f.write("\tchar *src[128][20];\n")
        f.write("\tchar *dest_temp[128][20];\n")
        f.write("\tfor(int loop_var=0; loop_var < sum_k; loop_var++)\n")
        f.write("{ \n")
        f.write("\tstrncpy(src[loop_var], temp_comm[loop_var], 6);\n")
        f.write("\tchar *tmp = strchr(temp_comm[loop_var], ' ');\n")
        f.write("\tif(tmp != NULL)\n")
        f.write("\tchar *dest_temp[loop_var]=tmp+1;\n")
        f.write("\tif(strlen(dest_temp[loop_var])>0)\n")
        f.write("\tcomm[loop_var] = dest_temp[loop_var];\n")
        #f.write("} \n")
        f.write('\tprintf("---------------------------");\n')
        f.write('\tprintf("%s",comm[loop_var]);\n')
        f.write('\tprintf("%s",task_name);\n')


        f.write("\tstruct stat pathout_check;\n")
        f.write("\t\tstat(pathout, &pathout_check);\n")
        f.write("\t\tif (!(S_ISDIR(pathout_check.st_mode)));\n")
        f.write("\t\tmkdir(pathout);\n")

        f.write("\tchar output_path=[];\n")
        f.write("\tif strcmp(task_name,src[loop_var])\n")
        f.write("{ \n")
        f.write('\tprintf("%s",comm[loop_var]);\n')
        f.write("\tchar output_list[128][128];\n")
        f.write("\tchar file_size[128][128];\n")
        f.write("\t\tchar new_file[128];\n")
        f.write('\tprintf("The neighor is:");\n')
        f.write('\tprintf("%s",comm[loop_var]);\n')
        f.write('\tprintf("The IDX  is:");\n')
        f.write('\tprintf("%s",src[loop_var]);\n')
        f.write("\tstrcpy(new_file,output_name);\n")
        f.write('\tstrcat(new_file,"_");\n')
        f.write("\tstrcat(new_file,src[loop_var]);\n")
        f.write("\toutput_list[j]=new_file;\n")
        f.write("\tfile_size[j]=comm[j];\n")
        f.write("\tchar* new_path[128]; \n")
        f.write("\tmemset(new_path, '\0', sizeof(new_path));\n")
        f.write("\tstrcpy(new_path,pathout);\n")
        f.write("\tstrcat(new_path,new_file);\n")
        f.write("\tstrcpy(output_path,new_path);\n")
        f.write('\tprintf("%s",new_path);\n')
        f.write("\tbash_script="/centralized_scheduler/generate_random_files.sh"; \n")                               
        f.write("\tstrcat(bash_script,new_path); \n")
	    f.write("\tstrcat(bash_script,file_size); \n")
	    f.write("\tsystem(bash_script); \n")
        f.write("} \n")                                                      #end of strcmp
        

        f.write("\telse if !strcmp(task_name,src[loop_var]) \n")
        f.write("\t \t {  \n") 
        f.write("\tstrcpy(new_file,output_name); \n")
        f.write('\tstrcat(new_file,"_"); \n')
        f.write("\tstrcat(new_file,task_name); \n")
        f.write("\tstrcpy(output_path,new_path);\n")
        f.write("\t file_size=itoa(rand() + 1);\n")
        f.write("\tstrcpy(new_file,output_name); \n")
	    f.write("\t bash_script="/centralized_scheduler/generate_random_files.sh"; \n")                               
        f.write("\tstrcat(bash_script,new_path); \n")
	    f.write("\tstrcat(bash_script,file_size); \n")
        f.write("\tsystem(bash_script); \n")                                      
        f.write("\t \t } \n") 
        f.write("\treturn output_path; \n")
        f.write("\t \t } \n") 
		
		
       
  f.write("\t int main() \n")
  f.write("\t \t {  \n") 
  f.write('\tchar filelist[128] = "1botnet.ipsum"; \n')
  f.write("\t \t char outpath[128]=dirname(__FILE__); \n")
  f.write('\t \t strcat(outpath,"sample_input/"); \n ')		
  f.write("\t char output_returned = task(filelist, outpath, outpath); \n")
  f.write("\treturn 0; \n")
  f.write("\t \t } \n")
		

def main():
   filelist = '1botnet.ipsum'
   outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
   subprocess.call(["gcc",filename])
   subprocess.call("./a.out")
	# outfile = task(filelist, outpath, outpath)
	# return outfile
    
    

