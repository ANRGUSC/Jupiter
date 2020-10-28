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

def retrieve_circe_logs():
    circe_namespace = app_config.namespace_prefix() + "-circe"
    export_log(circe_namespace)

def part_list_files(list_str,text,idx,shift=0):
    if shift == 0:
        list_files = list_str.split(text)[idx].split('-')   
        list_of_files = []
        for fi in list_files:
            tmp = fi.split('#')[1]+'img'+ classmap[fi.split('#')[0]]
            list_of_files.append(tmp)
        return list_of_files
    else:
        list_files = list_str.split(text)[idx][shift:].split('-')   
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
                    if re.search('runtime',line):
                        json_expr = '{'+line.split('{')[1]
                        runtime_dict =json.loads(json_expr)
                        try:
                            from_task,cur_task,fname = runtime_dict['filename'].split("_", maxsplit=3)
                        except Exception as e:
                            print('Something wrong in parsing')
                            print(e)
                        try:
                            if task_name.startswith('datasource'):
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
                                    list_of_imgs = part_list_files(fname,'score',1,2)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,cur_task,img)
                            elif task_name.startswith('lccdec'):
                                if runtime_dict['event']=='queue_start_process' or runtime_dict['event']=='new_input_file':
                                    list_of_imgs = part_list_files(fname,'score',1,2)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,from_task,img)
                                else:
                                    list_of_imgs = part_list_files(fname,'jobth',1)
                                    for img in list_of_imgs:
                                        append_log(runtime_dict,task_name,cur_task,img)
                        except Exception as e:
                            print(e)
                            print(runtime_dict) 


    return rt_datasource,rt_home,rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node


def find_runtime_task1(rt_dict,img_name, vtask1):
    res = []
    for task1, task2,img in rt_dict: 
        if (task1 == vtask1) and (img == img_name) :
            res.append(rt_dict[(task1, task2,img_name)])
    return res
def find_runtime_task2(rt_dict,img_name, vtask2):
    res = []
    for task1, task2,img in rt_dict: 
        if task2 == vtask2 and img == img_name :
            res.append(rt_dict[(task1, task2,img_name)])
    return res
def find_runtime_task1n2(rt_dict,img_name, vtask1,vtask2):
    res = []
    for task1, task2,img in rt_dict: 
        if task1==vtask1 and task2 == vtask2 and img == img_name :
            res.append(rt_dict[(task1, task2,img_name)])
    return res

def get_makespan_info(rt_home,rt_datasource):
    makespans_info = []
    for task_name,from_task,img in rt_home:
        res= find_runtime_task2(rt_datasource,img,'NA')[0]
        tmp = rt_home[(task_name,from_task,img)]-res
        makespans_info.append(tmp)
    return makespans_info

def get_communication_info(rt_datasource,rt_enter_node,rt_home):
    communication_info = dict()
    for task_name,from_task,img in rt_enter_node:
        if task_name=='master':
            res= find_runtime_task2(rt_datasource,img,'NA')[0]
            tmp = rt_enter_node[(task_name,from_task,img)]-res
            communication_info[('datasource','master',img)] = tmp
        elif task_name.startswith('lccdec'):
            tasknum = task_name.split('lccdec')[1]
            tmp = rt_home[('home',task_name,img)] - rt_enter_node[(task_name,'preagg'+tasknum,img)]
            communication_info[(task_name,'home',img)] = tmp
        else:
            child_tasks = app_config.child_tasks(task_name)
            if child_tasks is None: continue
            for c in child_tasks:
                r = find_runtime_task1(rt_enter_node,img,c)
                if len(r)==0: continue
                elif len(r)==1 :
                    communication_info[(task_name,c,img)] = -rt_enter_node[(task_name,from_task,img)] + r[0]
                else: 
                    r = find_runtime_task1n2(rt_enter_node,img, c,task_name)
                    if len(r)==0: continue
                    communication_info[(task_name,c,img)] = -rt_enter_node[(task_name,from_task,img)] + r[0]
    #print(communication_info)
    return communication_info


def gen_task_info(rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node):
    task_info = dict()
    # elapse_time ; pre_waiting_time ; execution_time ; post_waiting_time
    for task_name,from_task,img in rt_enter_node:
        try:
            exit_node = max(find_runtime_task1(rt_exit_node,img,task_name))
            elapse = exit_node- rt_enter_node[(task_name,from_task,img)]
            pre_waiting = rt_enter_queue[(task_name,from_task,img)]- rt_enter_node[(task_name,from_task,img)]
            exit_queue = max(find_runtime_task1(rt_enter_queue,img, task_name))
            execution = exit_queue - rt_enter_queue[(task_name,from_task,img)]
            post_waiting = exit_node - exit_queue
            task_info[(task_name,from_task,img)] = [elapse,pre_waiting,execution,post_waiting]
        except Exception as e:
            print('Something wrong!!!!')
            print(e)
            # print(task_name)
            # print(from_task)
            # print(img)

    return task_info

def calculate_info(rt_datasource,rt_home,rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node):
    # print(rt_home)
    # print(rt_datasource)
    # print(rt_enter_node)
    # print(rt_exit_node)
    # print(rt_enter_queue)
    # print(rt_exit_queue)
    makespans_info = get_makespan_info(rt_home,rt_datasource)    
    communication_info = get_communication_info(rt_datasource,rt_enter_node,rt_home)
    task_info = gen_task_info(rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node)
    percentage,percentage_part1,percentage_part2 = calculate_percentage(rt_datasource,rt_home,rt_exit_node)

    print('Percentage information')
    print(percentage)
    print(percentage_part1)
    print(percentage_part2)
    
    return makespans_info, communication_info,task_info

def calculate_percentage(rt_datasource,rt_home,rt_exit_node):
    all_inputs = dict()
    all_outputs_stage1 = dict()
    all_outputs_stage2 = dict()
    for i in range(1,ccdag.NUM_CLASS+1):
        all_inputs['datasource'+str(i)] = 0
        all_outputs_stage1['datasource'+str(i)] = 0
        all_outputs_stage2['datasource'+str(i)] = 0
    for task_name,from_task,img_name in rt_datasource:
        all_inputs[task_name] = all_inputs[task_name]+1
    for task_name,from_task,img_name in rt_home:
        num = from_task.split('lccdec')[1]
        all_outputs_stage2['datasource'+str(num)] = all_outputs_stage2['datasource'+str(num)]+1
    for task_name,dest_task,img_name in rt_exit_node:
        if task_name.startswith('storeclass'):
            num = task_name.split('storeclass')[1]
            all_outputs_stage1['datasource'+str(num)] = all_outputs_stage1['datasource'+str(num)]+1 
    percentage_part1 = dict()
    percentage_part2 = dict()
    percentage = dict()
    for ds in all_outputs_stage1:
        percentage_part1[ds] =  all_outputs_stage1[ds] /  all_inputs[ds]
        percentage_part2[ds] =  all_outputs_stage2[ds] /  all_outputs_stage1[ds]
        percentage[ds] = percentage_part2[ds]*percentage_part1[ds]

    return percentage,percentage_part1,percentage_part2




def plot_info(makespans_info, communication_info,task_info):
    os.makedirs('figures',exist_ok=True)
    #plot_makespan(makespans_info, TEST_INDICATORS)
    #plot_comm_times(communication_info, TEST_INDICATORS)
    plot_task_timings(task_info, TEST_INDICATORS)


def plot_makespan(makespan_info, file_prefix): 
    fig = plt.figure()
    plt.plot(makespan_info, '.')
    avg_makespan = mean(makespan_info)
    print("Average per-image makespan is: {}".format(avg_makespan))
    plt.title("{} scatterplot of per-image makespan".format(file_prefix) +
              "\n Average: {}".format(avg_makespan))
    plt.ylabel("seconds")
    plt.ylim(0, 300)
    plt.tight_layout()
    fig.savefig('figures/{}makespans.png'.format(file_prefix))


def plot_comm_times(communication_info, file_prefix):

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
            print(communication_info[k])
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

    master_exec_times = []
    master_wait_times = []
    resnet_exec_times = []
    resnet_wait_times = []
    # collage_exec_times = []
    # collage_wait_times = []
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
        # ['collage_exec_times', 'collage_wait_times'],
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

    print(task_info)

    for k, v in task_info.items():
        if k[0].startswith('master'):
            master_exec_times.append(float(v[2]))
            master_wait_times.append(float(v[1]))
        if k[0].startswith('resnet'):
            resnet_exec_times.append(float(v[2]))
            resnet_wait_times.append(float(v[1]))
        # if k[0].startswith('collage'):
        #     collage_exec_times.append(float(v[2]))
        #     collage_wait_times.append(float(v[1]))
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
        
        
        
        
        

    # straggling resnet logs don't hit home. manually insert them by parsing 
    # the raw resnet8 log files
    # try:
    #     with open(STRAGGLING_RESNET, 'r') as f:
    #         for line in f:
    #             if line.startswith('DEBUG:root:rt_enter '):
    #                 straggler_arriv_time = line.split()
    #                 straggler_arriv_time = float(straggler_arriv_time[-1])
    #             if line.startswith('DEBUG:root:rt_enter_task'):
    #                 straggler_start_time = line.split()
    #                 straggler_start_time = float(straggler_start_time[-1])
    #                 straggler_wait_time = straggler_start_time - straggler_arriv_time
    #                 resnet_wait_times.append(straggler_wait_time)
    #             if line.startswith('resnet_finish '): 
    #             # if line.startswith('DEBUG:root:rt_finish '): # use this if krishna's print statements aren't coming out
    #                 straggler_finish_time = line.split()
    #                 resnet_exec_time = float(straggler_finish_time[-1])  - straggler_start_time
    #                 resnet_exec_times.append(float(resnet_exec_time))
    # except FileNotFoundError:
    #     print("{} does not exist".format(STRAGGLING_RESNET))

    for task in task_and_statistic:
        fig = plt.figure()
        print(task[0])
        print(task[1])
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
    #retrieve_circe_logs()
    rt_datasource,rt_home,rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node = process_logs()
    makespans_info, communication_info,task_info = calculate_info(rt_datasource,rt_home,rt_enter_queue,rt_exit_queue,rt_enter_node,rt_exit_node)
    plot_info(makespans_info, communication_info,task_info)

    # COMM_TIMES = "filtered_logs/{}comm.log".format(TEST_INDICATORS)
    # MAKESPAN = "filtered_logs/{}makespan.log".format(TEST_INDICATORS)
    # TASK_TIMES = "filtered_logs/{}task.log".format(TEST_INDICATORS)
    # STRAGGLING_RESNET = "filtered_logs/{}resnet8.log".format(TEST_INDICATORS)
    # MASTER_SERVICE = "filtered_logs/{}master.log".format(TEST_INDICATORS)

    # os.makedirs('figures', exist_ok=True)

    # print("Graphing and calculating averages for test {}".format(TEST_INDICATORS))

    # # try:
    # #     with open(TASK_TIMES, 'r') as f:
    # #         task_info = eval(f.read())
    # #         plot_task_timings(task_info, TEST_INDICATORS)
    # # except FileNotFoundError:
    # #     print("{} does not exist".format(TASK_TIMES))

    # # try:
    # #     with open(COMM_TIMES, 'r') as f:
    # #         comm_log = eval(f.read())
    # #         plot_comm_times(comm_log, TEST_INDICATORS)
    # # except FileNotFoundError:
    # #     print("{} does not exist".format(COMM_TIMES))

    # try:
    #     with open(MAKESPAN, 'r') as f:
    #         makespan_log = eval(f.read())
    #         plot_makespan(makespan_log, TEST_INDICATORS)
    # except FileNotFoundError:
    #     print("{} does not exist".format(MAKESPAN))

    #plt.show()