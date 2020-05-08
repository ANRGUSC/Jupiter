#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<math.h>
#include<time.h>
#include<sys/stat.h>
#include<sys/types.h>
#define PATH_MAX 128
#include<libgen.h>
#include<stdint.h>
#include<inttypes.h>
#define LSIZ 128 
#define RSIZ 20


char file_path[RSIZ][LSIZ];
int execution_time;
char task_name_temp[LSIZ];
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
//char** keys;

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

 char** task(char* filename,char* pathin,char* pathout)
{ 
	execution_time = rand() % 10;
	printf("%d\n",execution_time);
	time_t timeout=0;
	timeout = time(&timeout) + execution_time;
	while (time(&timeout) < timeout)
  { 
		1+1 ;
  } 
	char *path = basename(__FILE__);
	char *path_cpy = strdup(path);
	
        memcpy(task_name_temp,path_cpy,LSIZ);
        char* token = strtok(task_name_temp,".");
        memcpy(task_name,token,LSIZ);
	printf("-------------------------\n");
	printf("%s\n",task_name);
	printf("%s\n",filename);
	printf("-------------------------\n" );
	strcpy(output1_list,filename);
	strcat(output1_list,"_");
	strcat(output1_list,task_name);
	strcat(output1_list,".txt") ; 
             
	printf("%s\n",output1_list);
        strcpy(input_file,filename);
	printf("%s\n",input_file);
	strcpy(output_name,input_file);
        strcat(output_name,"_");
	strcat(output_name,task_name);	
        printf("%s\n",output_name);
	printf("---------------------------\n");
	char actualpath [PATH_MAX+1];
	char *file_comm = "communication.txt";
	char *ptr;
        
        
	ptr=realpath(file_comm,actualpath);
	printf("%s\n",actualpath);

       char** keys=(char**)malloc(sizeof(char*)*RSIZ);
       for(int lnVar=0;lnVar< RSIZ;lnVar++)
    {
        keys[lnVar]=(char*)malloc(LSIZ);
    }
	
     
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
                    int j = 0;
                    pch = strtok (str," -");
                    while (pch != NULL)
                    {
                          if(j%2 == 0)
                          {
                              
                              strcpy(dest[idx1], pch);
                              idx1++;
                          }
                          else
                          {
                              
                               strcpy (sizes[idx2],pch);
                               idx2++;
                          }
                          j++;
      
                          pch = strtok (NULL, " -");
                    }   //while loop

                    for(int k = 0;k < idx1; k++)
                    {
                        memset(bash_script,'\0',sizeof(bash_script));
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
			strcat(bash_script," ");
                        strcat(bash_script,new_path);
			strcat(bash_script," ");
                        int dev;
			sscanf(sizes[k], "%d",&dev);
                       //printf("DEV************%dn",dev);
                        char s[LSIZ];
                        sprintf(s,"%d",dev);
                        strcat(bash_script,s);
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
              strcat(bash_script," ");
              strcat(bash_script,new_path);
              strcat(bash_script," ");
              strcat(bash_script,rand_file);
              
              system(bash_script);
        } 
        
        for(int x=0; x< idx1; x++)
        {
          strcpy(keys[x],output_path[x]);
        }

     return keys;
}

	 char** main() 
	 {  
       
	char filelist[128] = "1botnet.ipsum";  
        
	char* outpath="/centralized_scheduler/sample_input/";
        char** final = (char**)malloc(RSIZ*sizeof(char *));
        for(int i=0; i<RSIZ; i++)
        {
         final[i]=(char*)malloc(LSIZ*sizeof(char));
        }
          //s = (char**)malloc(RSIZ*sizeof(char *));
 
        final= task(filelist, outpath, outpath);
        
      
        return final;
 
     
	
	 } 
