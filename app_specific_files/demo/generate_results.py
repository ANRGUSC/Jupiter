import os
import sys
import matplotlib.pyplot as plt
from statistics import mean
import signal
from kubernetes.client.apis import core_v1_api
from kubernetes import client, config
sys.path.append("../../")
import jupiter_config
import json
import re
import numpy as np
import json

try:
    # successful if running in container
    sys.path.append("/jupiter/build")
    sys.path.append("/jupiter/build/app_specific_files/")
    from jupiter_utils import app_config_parser
except ModuleNotFoundError:
    # Python file must be running locally for testing
    sys.path.append("../../core/")
    from jupiter_utils import app_config_parser

import ccdag

# SEE README.md for more information on naming conventions!

# these are the filenames to process, all dictated by TEST_INDICATORS
# First two binary digits indicate the test flags for coding
# Letters indicate test number (to differentiate from the flags)
# postfix "sleep" indicates if artificial sleeps are injected in the test
# examples: "11a", "01a", "01b" "01a-sleep"
TEST_INDICATORS = "%d%d%s-%s"%(ccdag.CODING_PART1,ccdag.CODING_PART2,ccdag.EXP_ID,ccdag.EXP_NAME)
print(TEST_INDICATORS)
# see how file names are structured in main

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)
config.load_kube_config(config_file=jupiter_config.get_kubeconfig())
core_v1_api = client.CoreV1Api()
os.makedirs("results", exist_ok=True)
results_path="results/%s"%(TEST_INDICATORS)
os.makedirs(results_path, exist_ok=True)


classid = np.arange(0,len(ccdag.classlist),1)
classid = [str(x) for x in classid]
classmap = dict(zip(classid,ccdag.classlist))



rt_enter_node = dict()
rt_exit_node = dict()
rt_enter_queue = dict()
rt_exit_queue = dict()
rt_datasource = dict()
rt_home = dict()

def export_log(namespace):
    resp = core_v1_api.list_namespaced_pod(namespace)
    if resp.items:
        for item in resp.items:
            name = item.metadata.name
            file_name = '%s/%s.log'%(results_path,name)
            cmd = 'kubectl logs -n%s %s > %s'%(namespace,name,file_name)
            os.system(cmd)

def retrieve_logs(module):
    namespace = app_config.namespace_prefix() + "-"+module
    export_log(namespace)

def part_list_files(list_str,text,idx,check=0):
    if check == 0:
        list_files = list_str.split(text)[idx].split('-')   
        list_of_files = []
        for fi in list_files:
            tmp = fi.split('#')[1]+'img'+ classmap[fi.split('#')[0]]
            list_of_files.append(tmp)
        return list_of_files
    else:
        a = list_str.split(text)[idx]
        idx1 = a.find(next(filter(str.isalpha, a)))
        list_files = a[idx1+1:].split('-')  
        list_of_files = []
        for fi in list_files:
            tmp = fi.split('#')[1]+'img'+ classmap[fi.split('#')[0]]
            list_of_files.append(tmp)
        return list_of_files

def append_log(runtime_dict,task1,task2,fname):
    if runtime_dict['task_name']=='circe' and runtime_dict['event']=='new_input_file':   
        rt_enter_node[(task1,task2,fname)] = runtime_dict['unix_time']
    elif runtime_dict['task_name']==task1 and runtime_dict['event']=='queue_start_process':
        rt_enter_queue[(task1,task2,fname)] = runtime_dict['unix_time']
    elif runtime_dict['task_name']=='circe' and runtime_dict['event']=='new_output_file':
        rt_exit_node[(task1,task2,fname)] = runtime_dict['unix_time']
    elif runtime_dict['task_name']==task1 and runtime_dict['event']=='queue_end_process':
        rt_exit_queue[(task1,task2,fname)] = runtime_dict['unix_time']
    
def process_logs():
    for (dirpath, dirnames, filenames) in os.walk(results_path):
        for filename in filenames:
            task_name = filename.split('-')[1]
            filepath=os.sep.join([dirpath, filename])
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if re.search('runtime',line):
                        json_expr = '{'+line.split('{')[1]
                        runtime_dict =json.loads(json_expr)  
                        try:
                            from_task,cur_task,fname = runtime_dict['filename'].split("_", maxsplit=3)
                            if task_name.startswith('datasource') and runtime_dict['event']=='new_output_file':
                                img_name = fname.split('.')[0]
                                rt_datasource[(task_name,'NA',img_name)] = runtime_dict['unix_time']
                            elif task_name=='home':
                                list_of_imgs = part_list_files(fname,'jobth',1)
                                for img in list_of_imgs:
                                    rt_home[(cur_task,from_task,img)] = runtime_dict['unix_time']
                            elif task_name=='collage':
                                list_of_imgs = part_list_files(fname,'job',0)
                                for img in list_of_imgs:
                                    append_log(runtime_dict,task_name,from_task,img)
                            elif task_name=='master':
                                if runtime_dict['event']=='queue_start_process' or runtime_dict['event']=='new_input_file':
                                    img_name = fname.split('.')[0]
                                    append_log(runtime_dict,task_name,from_task,img_name)
                                else:
                                    task_name,dest_task,fname = runtime_dict['filename'].split("_", maxsplit=3)
                                    if dest_task=='collage':
                                        list_of_imgs = part_list_files(fname,'job',0)
                                        for img in list_of_imgs:
                                            append_log(runtime_dict,task_name,dest_task,img)
                                    else:
                                        img_name = fname.split('job')[0]
                                        append_log(runtime_dict,task_name,dest_task,img_name)
                            elif task_name.startswith('resnet') or task_name.startswith('store'):
                                img_name = fname.split('job')[0]
                                if runtime_dict['event']=='queue_start_process' or runtime_dict['event']=='new_input_file':
                                    append_log(runtime_dict,task_name,from_task,img_name)
                                else:
                                    append_log(runtime_dict,task_name,cur_task,img_name)
                            elif task_name.startswith('lccenc'):
                                if runtime_dict['event']=='queue_end_process':
                                    list_of_imgs = part_list_files(fname,'job',0)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,cur_task,img)
                                else:
                                    if runtime_dict['event']=='new_output_file':
                                        list_of_imgs = part_list_files(fname,'job',0)
                                        for img in list_of_imgs:
                                            append_log(runtime_dict,task_name,cur_task,img)
                                    else:
                                        img_name = fname.split('job')[0]
                                        append_log(runtime_dict,task_name,from_task,img_name)
                            elif task_name.startswith('score'):
                                if runtime_dict['event']=='queue_start_process' or runtime_dict['event']=='new_input_file':
                                    list_of_imgs = part_list_files(fname,'job',0)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,from_task,img)
                                else:
                                    list_of_imgs = part_list_files(fname,'jobth',1)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,cur_task,img)
                            elif task_name.startswith('preagg'):
                                if runtime_dict['event']=='queue_start_process' or runtime_dict['event']=='new_input_file':
                                    list_of_imgs = part_list_files(fname,'jobth',1)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,from_task,img)
                                else:
                                    list_of_imgs = part_list_files(fname,'score',1,1)
                                    
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,cur_task,img)
                            elif task_name.startswith('lccdec'):
                                if runtime_dict['event']=='queue_start_process' or runtime_dict['event']=='new_input_file':
                                    list_of_imgs = part_list_files(fname,'score',1,1)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,from_task,img)
                                else:
                                    list_of_imgs = part_list_files(fname,'jobth',1)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,cur_task,img)
                            else:
                                print('Task name not recognized or non-important log')
                                #print(runtime_dict)
        

                        except Exception as exc:
                            print('Something wrong in processing tasks')
                            print(task_name)
                            


    return rt_datasource,rt_home,rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node


def find_runtime_task1(rt_dict,img_name, vtask1):
    res = []
    task2_list = []
    for task1, task2,img in rt_dict: 
        if (task1 == vtask1) and (img == img_name) :
            res.append(rt_dict[(task1, task2,img_name)])
            task2_list.append(task1)
    return res,task2_list
def find_runtime_task2(rt_dict,img_name, vtask2):
    res = []
    task1_list = []
    for task1, task2,img in rt_dict: 
        if task2 == vtask2 and img == img_name :
            res.append(rt_dict[(task1, task2,img_name)])
            task1_list.append(task1)
    return res,task1_list
def find_runtime_task1n2(rt_dict,img_name, vtask1,vtask2):
    res = []
    for task1, task2,img in rt_dict: 
        if task1==vtask1 and task2 == vtask2 and img == img_name :
            res.append(rt_dict[(task1, task2,img_name)])
    return res

def get_makespan_info(rt_home,rt_datasource):
    makespans_info = []
    for task_name,from_task,img in rt_home:
        res,_= find_runtime_task2(rt_datasource,img,'NA')
        tmp = rt_home[(task_name,from_task,img)]-res[0]
        makespans_info.append(tmp)
    return makespans_info

def get_communication_info(rt_datasource,rt_enter_node,rt_home):
    communication_info = dict()
    for task_name,from_task,img in rt_enter_node:
        if task_name == 'master':
            res,ds= find_runtime_task2(rt_datasource,img,'NA')
            if len(res) == 0:
                continue
            tmp = rt_enter_node[(task_name,from_task,img)] - min(res)
            communication_info[('datasource','master',img)] = tmp
    for task_name,dest_task,img in rt_exit_node:
        if task_name.startswith('lccdec'): 
            try:
                r = find_runtime_task1n2(rt_home,img, 'home',task_name)
                if len(r) == 0:
                    print('File did not enter the home node!!!')
                    print(task_name)
                    print(img)
                    # exit()
                elif len(r) == 1:
                    communication_info[(task_name,'home',img)] = - rt_exit_node[(task_name,'home',img)] + r[0]
            except Exception as e:
                print('Something wrong !!!!')
        else:
            try:
                r = find_runtime_task1n2(rt_enter_node,img, dest_task,task_name)
                if len(r) == 0:
                    print('File did not enter the children node!!!')
                elif len(r) == 1:
                    communication_info[(task_name,dest_task,img)] = - rt_exit_node[(task_name,dest_task,img)] + r[0]
            except Exception as e:
                print('Something wrong!!!')
    return communication_info



def gen_task_info(rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node):
    task_info = dict()
    # elapse_time ; pre_waiting_time ; execution_time ; post_waiting_time
    for task_name,dest_task,img in rt_exit_queue:
        try:
            if task_name == 'collage': #no output file
                exit_node = rt_exit_queue[(task_name,dest_task,img)]
            else:
                exit_node = rt_exit_node[(task_name,dest_task,img)]
            res,_ = find_runtime_task1(rt_enter_node,img,task_name)
            enter_node = min(res)
            res,_ =find_runtime_task1(rt_enter_queue,img,task_name)
            enter_queue = min(res)
            elapse = exit_node- enter_node
            pre_waiting = enter_queue - enter_node
            execution = rt_exit_queue[task_name,dest_task,img] - enter_queue
            task_info[(task_name,dest_task,img)] = [elapse,pre_waiting,execution]
        except Exception as e:
            print('File does not enter the children node for task info!!!!')
            pass
            #exit()
    #print(task_info)
    return task_info

def calculate_info(rt_datasource,rt_home,rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node):
    makespans_info = dict()
    communication_info = dict()
    task_info = dict()

    makespans_info = get_makespan_info(rt_home,rt_datasource)    
    communication_info = get_communication_info(rt_datasource,rt_enter_node,rt_home)
    task_info = gen_task_info(rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node)

    # print('******************** Makespan information *************************')
    # print(makespans_info)
    # print('******************* Communication information *********************')
    # print(communication_info)
    # print('******************* Task information ******************************')
    # print(task_info)
    
    return makespans_info, communication_info,task_info

def calculate_percentage(rt_datasource,rt_home,rt_exit_node):
    percentage,percentage_part1,percentage_part2 = 0,0,0
    sum_input,sum_stage1,sum_stage2 = 0,0,0
    set_input = set()
    set_stage1 = set()
    set_stage2 = set()
    for task_name,from_task,img_name in rt_datasource:
        if img_name not in set_input:
            set_input.add(img_name)
            sum_input = sum_input+1
    for task_name,from_task,img_name in rt_home:
        if img_name not in set_stage2:
            set_stage2.add(img_name)
            sum_stage2 = sum_stage2+1
    for task_name,dest_task,img_name in rt_exit_node:
        if task_name.startswith('storeclass'):
            if img_name not in set_stage1:
                set_stage1.add(img_name)
                sum_stage1 = sum_stage1+1

    print('---- Number of processed images: ----')
    print(TEST_INDICATORS)
    print(sum_input)
    print(sum_stage1)
    print(sum_stage2)
    percentage_part1 = 100 * sum_stage1/sum_input
    percentage_part2 = 100 * sum_stage2/sum_stage1
    percentage = 100 * sum_stage2/sum_input
    return percentage,percentage_part1,percentage_part2




def plot_info(makespans_info, communication_info,task_info):
    os.makedirs('figures',exist_ok=True)
    plot_makespan(makespans_info, TEST_INDICATORS)
    plot_comm_times(communication_info, TEST_INDICATORS)
    plot_task_timings(task_info, TEST_INDICATORS)


def plot_makespan(makespan_info, file_prefix): 
    print('Plotting makespan')
    fig = plt.figure()
    plt.plot(makespan_info, '.')
    avg_makespan = mean(makespan_info)
    print("Average per-image makespan is: {}".format(avg_makespan))
    plt.title("{} scatterplot of per-image makespan".format(file_prefix) +
              "\n Average: {}".format(avg_makespan))
    plt.ylabel("seconds")
    print('************************ Plot makespan')
    plt.ylim(0, 1800)
    plt.tight_layout()
    fig.savefig('figures/{}makespans.png'.format(file_prefix))


def plot_comm_times(communication_info, file_prefix):
    print('Plotting Communication times')

    datasource_to_master = []
    master_to_resnet = []
    master_to_collage = []   
    resnet_to_storeclass = []
    storeclass_to_lccenc = []
    lccenc_to_score = []
    score_to_preagg = []
    preagg_to_lccdec = []
    lccdec_to_home = []


    for k, v in communication_info.items():
        if k[1].startswith('master') and k[0].startswith('datasource'):
            datasource_to_master.append(v)
        if k[0].startswith('master') and k[1].startswith('resnet'):
            master_to_resnet.append(v)
        if k[0].startswith('master') and k[1].startswith('collage'):
            master_to_collage.append(v)
        if k[0].startswith('resnet') and k[1].startswith('storeclass'):
            resnet_to_storeclass.append(v)
        if k[0].startswith('store') and k[1].startswith('lccenc'):
            storeclass_to_lccenc.append(v)
        if k[0].startswith('lccenc') and k[1].startswith('score'):
            lccenc_to_score.append(v)
        if k[0].startswith('score') and k[1].startswith('preagg'):
            score_to_preagg.append(v)
        if k[0].startswith('preagg') and k[1].startswith('lccdec'):
            preagg_to_lccdec.append(v)
        if k[0].startswith('lccdec') and k[1].startswith('home'):
            lccdec_to_home.append(v)



    source_to_dest = ['datasource_to_master', 'master_to_resnet', 'master_to_collage',
    'resnet_to_storeclass', 'storeclass_to_lccenc', 'lccenc_to_score', 
    'score_to_preagg', 'preagg_to_lccdec','lccdec_to_home']

    for src_dst in source_to_dest:
        if not eval(src_dst):
            print("no logs found for {}!", src_dst)
            continue
        fig = plt.figure()
        plt.plot(eval(src_dst), '.')
        average = mean(eval(src_dst))
        print("Comm: average of {} is {} seconds".format(src_dst, average))
        plt.title("{} {} communication time vs job\naverage = {}s"
                  .format(file_prefix, src_dst, average))
        plt.ylabel("seconds")
        plt.tight_layout()
        fig.savefig('figures/{}_{}_comm_times.png'
                    .format(file_prefix, src_dst))


def plot_task_timings(task_info, file_prefix):

    print('Plot task timings')
    master_exec_times = []
    master_wait_times = []
    resnet_exec_times = []
    resnet_wait_times = []
    collage_exec_times = []
    collage_wait_times = []
    store_exec_times = []
    store_wait_times = []

    
    lccenc_exec_times = []
    lccenc_wait_times = []
    score_exec_times = []
    score_wait_times = []
    preagg_exec_times = []
    preagg_wait_times = []
    lccdec_exec_times = []
    lccdec_wait_times = []
    
    task_and_statistic = [
        ['master_exec_times', 'master_wait_times'], 
        ['resnet_exec_times', 'resnet_wait_times'],
        ['collage_exec_times', 'collage_wait_times'],
        ['store_exec_times', 'store_wait_times'],
        ['lccenc_exec_times', 'lccenc_wait_times'],
        ['score_exec_times', 'score_wait_times'],
        ['preagg_exec_times', 'preagg_wait_times'],
        ['lccdec_exec_times', 'lccdec_wait_times'],
    ]  

    # keys are tuples:
    # ('task_name','local_input_file')

    # NOTE: service_time = execution_time = processing time for a job minus wait times
    # values are a list:
    # ['enter_time','proc_create_time','proc_exit_time', 'elapse_time',
    # 'duration_time','waiting_time','service_time', 'wait_time',
    # 'proc_shutdown_interval']

    for k, v in task_info.items():
        if k[0].startswith('master'):
            master_exec_times.append(float(v[2]))
            master_wait_times.append(float(v[1]))
        if k[0].startswith('resnet'):
            resnet_exec_times.append(float(v[2]))
            resnet_wait_times.append(float(v[1]))
        if k[0].startswith('collage'):
            collage_exec_times.append(float(v[2]))
            collage_wait_times.append(float(v[1]))
        if k[0].startswith('store'):
            store_exec_times.append(float(v[2]))
            store_wait_times.append(float(v[1]))
        if k[0].startswith('lccenc'):
            lccenc_exec_times.append(float(v[2]))
            lccenc_wait_times.append(float(v[1]))
        if k[0].startswith('score'):
            score_exec_times.append(float(v[2]))
            score_wait_times.append(float(v[1]))
        if k[0].startswith('preagg'):
            preagg_exec_times.append(float(v[2]))
            preagg_wait_times.append(float(v[1]))
        if k[0].startswith('lccdec'):
            lccdec_exec_times.append(float(v[2]))
            lccdec_wait_times.append(float(v[1]))
        
    for task in task_and_statistic:
        fig = plt.figure()
        plt.plot(eval(task[0]), '.')
        plt.plot(eval(task[1]), 'y+')
        exec_time_avg = mean(eval(task[0]))
        print("{} average is {}s".format(task[0], exec_time_avg))
        wait_time_avg = mean(eval(task[1]))
        print("{} average is {}s".format(task[1], wait_time_avg))
        plt.title(
            "{} {} execution times (.) and wait times (+) vs. job instance".format(file_prefix, task[0][0:6]) +
            "\nexecution time avg = {}".format(exec_time_avg) +
            "\nwait time avg = {}".format(wait_time_avg)
        )
        plt.ylabel("seconds")
        plt.tight_layout()
        fig.savefig('figures/{}_{}_exec_times.png'.format(file_prefix, task[0][0:6]))

if __name__ == '__main__':
    # retrieve_logs('circe')
    # retrieve_logs('profiler')
    # retrieve_logs('exec')
    # retrieve_logs('mapper')
    rt_datasource,rt_home,rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node = process_logs()
    print('----------- Datasource----------------')
    print(rt_datasource)
    print('----------- Home ----------------')
    print(rt_home)
    print('----------- Enter Queue ----------------')
    print(rt_enter_queue)
    print('----------- Exit Queue ----------------')
    print(rt_exit_queue)
    print('----------- Enter Node ----------------')
    print(rt_enter_node)
    print('----------- Exit Node ----------------')
    print(rt_exit_node)

    makespans_info, communication_info,task_info = calculate_info(rt_datasource,rt_home,rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node) 
    percentage,percentage_part1,percentage_part2 = calculate_percentage(rt_datasource,rt_home,rt_exit_node)

    print('******************** Percentage information ************************')
    print('Percentage part 1')
    print(percentage_part1)
    print('Percentage part 2')
    print(percentage_part2)
    print('Percentage')
    print(percentage)
    
    plot_info(makespans_info, communication_info,task_info)