#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<math.h>
#include<time.h>
#include<sys/stat.h>
#include<sys/types.h>
#define PATH_MAX 128
#include<libgen.h>
#define LSIZ 128 
#define RSIZ 20

char* filename="task3.c";
char file_path[RSIZ][LSIZ];
int execution_time;
char task_name[LSIZ];
char output1_list[LSIZ];
char input_file[LSIZ];
char output_name[LSIZ];
char new_path[LSIZ];
char bash_script[LSIZ];
int loop_var;
char* ptr;
char* base;
char rand_file[50];
char output_path[RSIZ][LSIZ];
char output_list[RSIZ][LSIZ];
char file_size[RSIZ][LSIZ];
char new_file[LSIZ];

char line[RSIZ][LSIZ];
char temp_comm [RSIZ][LSIZ];
char src[RSIZ][LSIZ];
char comm[RSIZ][LSIZ];
char dest_temp[RSIZ][LSIZ];
char dest[RSIZ][LSIZ];
char sizes[RSIZ][LSIZ];
char str[LSIZ];
char* fname;
FILE *fptr = NULL; 
int i = 0;
int k=0;
int flag=0;
static int tot = 0;
int idx1 = 0, idx2 = 0;

 char* task(char* filename,char* pathin,char* pathout)
{ 
	execution_time = rand() % 10;
	printf("%d\n",execution_time);
	time_t timeout=0;
	timeout = time(&timeout) + execution_time;
	while (time(&timeout) < timeout)
  { 
		1+1 ;
  } 
	char *path = "/Desktop/testshraddha/task3";
	char *path_cpy = strdup(path);
	base=basename(path_cpy);
        memcpy(task_name,base,LSIZ);
	printf("-------------------------\n");
	printf("%s\n",task_name);
	printf("%s\n",filename);
	printf("-------------------------\n" );
	strcpy(output1_list,filename);
	strcat(output1_list,"_");
	strcat(output1_list,task_name);
	strcat(output1_list,".txt") ;      
	printf("%s\n",output1_list);
	printf("%s\n",input_file);
	strcpy(output_name,input_file);
        strcat(output_name,"_");
	strcat(output_name,task_name);	
        printf("%s\n",output_name);
	printf("---------------------------\n");
	char actualpath [PATH_MAX+1];
	char *file_comm = "/Desktop/testshraddha/communication.txt";
	char *ptr;
        //memset(ptr,'\0', sizeof(ptr));
        
	ptr=realpath(file_comm,actualpath);
	printf("%s\n",actualpath);


 
    fname="communication.txt";	

    fptr = fopen(fname, "r");
    while(fgets(line[i], LSIZ, fptr)) 
    {
        line[i][strlen(line[i]) - 1] = '\0';   
        strcpy(temp_comm[i], line[i]);
        i++;
    }
    tot = i;
       
    for(i = 0; i < tot; ++i)
    {
        
        strncpy(src[i], temp_comm[i], 6);
        char *tmp = strchr(temp_comm[i], ' ');
        if(tmp!=NULL)
        {
               strcpy(dest_temp[i],tmp+1);
               if(strlen(dest_temp[i])>0)
                 {
                    strcpy(comm[i] ,dest_temp[i]);
                  }
        }
    }
    for(i = 0; i < tot; ++i)
    {
      if (strncmp(task_name,src[i],5)==0)
      {   
                    strcpy(str, comm[i]);
                    char* pch;
                    //memset(pch,'\0', sizeof(pch));
                    int j = 0;
                    pch = strtok (str," -");
                    while (pch != NULL)
                    {
                          if(j%2 == 0)
                          {
                              //printf ("*********dest:************%s\n",pch);
                              strcpy(dest[idx1], pch);
                              idx1++;
                          }
                          else
                          {
                              // printf ("-----------size:----------%s\n",pch);
                               strcpy (sizes[idx2],pch);
                               idx2++;
                          }
                          j++;
      
                          pch = strtok (NULL, " -");
                    }   //while loop

                    for(int k = 0;k < idx1; k++)
                    {
                        printf("The neighor is:\n");
                        printf("%s\n",dest[k]);
                        printf("The IDX  is:\n");
                        printf("%d\n",k);
                        strcpy(new_file,output_name);
                        strcat(new_file,"_");
                        strcat(new_file,dest[k]);
                        strcpy(output_list[k],new_file);
                        strcpy(file_size[k],sizes[k]);
                        char new_path[LSIZ]; 
                        //memset(new_path,'\0', sizeof(new_path));
                        strcpy(new_path,pathout);
                        strcat(new_path,new_file);
                        strcpy(output_path[k],new_path);
                        printf("NEW PATH IS %s \n",new_path);
                        strcat(bash_script,"/centralized_scheduler/generate_random_files.sh"); 
                        strcat(bash_script,new_path);
                        strcat(bash_script,sizes[k]);
                        system(bash_script); 
                    }
        } // END OF STRCMP IF
	else if((strncmp(task_name,src[i],5)!=0))
		flag++;
}// close of for

        if(flag == tot)
        {      
              int k=0;
              strcpy(new_file,output_name); 
              strcat(new_file,"_"); 
              strcat(new_file,task_name);
	      char new_path[LSIZ]; 
              strcpy(new_path,pathout);
              strcat(new_path,new_file);
              strcpy(output_path[k],new_path);
              int x= (rand() + 1);
              sprintf(rand_file,"%d",x);
              strcpy(new_file,output_name); 
              strcat(bash_script,"/centralized_scheduler/generate_random_files.sh"); 
              strcat(bash_script,new_path);
              strcat(bash_script,rand_file);
              system(bash_script); 
        } 
   
     return (char *)output_path;
}

	 char* main() 
	 {  
        /*memset(file_path,'\0', sizeof(file_path)); 
        //memset(task_name,'\0', sizeof(task_name));
        //memset(output1_list,'\0', sizeof(output1_list));
        //memset(input_file,'\0', sizeof(input_file));
        memset(output_name,'\0', sizeof(output_name));
        memset(new_path,'\0', sizeof(new_path));
        //memset(bash_script,'\0', sizeof(bash_script));
        memset(ptr,'\0', sizeof(ptr));
        memset(base,'\0', sizeof(base));
        memset(rand_file,'\0', sizeof(rand_file));
        memset(output_path,'\0', sizeof(output_path));
        memset(output_list,'\0', sizeof(output_list));
        memset(file_size,'\0', sizeof(file_size));
        memset(new_file,'\0', sizeof(new_file));
        memset(line,'\0', sizeof(line));
        memset(comm,'\0', sizeof(comm));
        memset(temp_comm,'\0', sizeof(temp_comm));
        memset(src,'\0', sizeof(src));
        memset(dest,'\0', sizeof(dest));
        memset(dest_temp,'\0', sizeof(dest_temp));
        memset(sizes,'\0', sizeof(sizes));
        memset(str,'\0', sizeof(str));
        memset(fname,'\0', sizeof(fname)); */
	char filelist[128] = "1botnet.ipsum";  
	char* outpath="/Desktop/testshraddha";
	//strcat(outpath,"sample_input/"); 
        char* final= task(filelist, outpath, outpath);
         for(int v=0;v<tot;v++)
      {
          printf("OUTPUT PATH: %s\n",output_path[v]);
      }   
        
               
	
	 } 
