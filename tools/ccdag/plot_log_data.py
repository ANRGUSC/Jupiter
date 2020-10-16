import os
import sys
import matplotlib.pyplot as plt
from statistics import mean
import signal

# SEE README.md for more information on naming conventions!

# these are the filenames to process, all dictated by TEST_INDICATORS
# First two binary digits indicate the test flags for coding
# Letters indicate test number (to differentiate from the flags)
# postfix "sleep" indicates if artificial sleeps are injected in the test
# examples: "11a", "01a", "01b" "01a-sleep"
TEST_INDICATORS = "00z-sleep"
# see how file names are structured in main

def signal_handler(sig, frame):
    print("Ctrl+c detected, exiting and closing all plots...")
    sys.exit(0)

def plot_makespan(makespan_log, file_prefix):

    makespans = []

    for k, v in makespan_log.items():
        makespans.append(v)

    fig = plt.figure()
    plt.plot(makespans, '.')
    avg_makespan = mean(makespans)
    print("Average per-image makespan is: {}".format(avg_makespan))
    plt.title("{} scatterplot of per-image makespan".format(file_prefix) +
              "\n Average: {}".format(avg_makespan))
    plt.ylabel("seconds")
    plt.ylim(0, 300)
    plt.tight_layout()
    fig.savefig('figures/{}makespans.png'.format(file_prefix))


def plot_comm_times(comm_log, file_prefix):
    datasource_to_master = []
    master_to_resnet = []   
    resnet_to_storeclass = []
    storeclass_to_lccenc = []
    lccenc_to_score = []
    score_to_preagg = []
    preagg_to_lccdec = []
    lccdec_to_home = []

    source_to_dest = ['datasource_to_master', 'master_to_resnet', 
    'resnet_to_storeclass', 'storeclass_to_lccenc', 'lccenc_to_score', 
    'score_to_preagg', 'preagg_to_lccdec', 'lccdec_to_home']

    for k, v in comm_log.items():
        if k[2].startswith('master') and k[1].startswith('datasource'):
            datasource_to_master.append(v)
        if k[2].startswith('master') and k[1].startswith('resnet'):
            master_to_resnet.append(v)
        if k[2].startswith('resnet') and k[1].startswith('storeclass'):
            resnet_to_storeclass.append(v)
        if k[2].startswith('storeclass') and k[1].startswith('lccenc'):
            storeclass_to_lccenc.append(v)
        if k[2].startswith('lccenc') and k[1].startswith('score'):
            lccenc_to_score.append(v)
        if k[2].startswith('score') and k[1].startswith('preagg'):
            score_to_preagg.append(v)
        if k[2].startswith('lccdec') and k[1].startswith('preagg'):
            preagg_to_lccdec.append(v)
        if k[2].startswith('home') and k[1].startswith('lccdec'):
            lccdec_to_home.append(v)


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


def plot_task_timings(task_log, file_prefix):

    lccdec_exec_times = []
    lccdec_wait_times = []
    lccenc_exec_times = []
    lccenc_wait_times = []
    master_exec_times = []
    master_wait_times = []
    preagg_exec_times = []
    preagg_wait_times = []
    resnet_exec_times = []
    resnet_wait_times = []
    score_exec_times = []
    score_wait_times = []
    storeclass_exec_times = []
    storeclass_wait_times = []

    task_and_statistic = [
        ['master_exec_times', 'master_wait_times'], 
        ['resnet_exec_times', 'resnet_wait_times'],
        ['storeclass_exec_times', 'storeclass_wait_times'],
        ['score_exec_times', 'score_wait_times'], 
        ['lccenc_exec_times', 'lccenc_wait_times'],
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

    for k, v in task_log.items():
        if k[0].startswith('lccdec'):
            lccdec_exec_times.append(float(v[6]))
            lccdec_wait_times.append(float(v[7]))
        if k[0].startswith('lccenc'):
            lccenc_exec_times.append(float(v[6]))
            lccenc_wait_times.append(float(v[7]))
        if k[0].startswith('master'):
            master_exec_times.append(float(v[6]))
            master_wait_times.append(float(v[7]))
        if k[0].startswith('preagg'):
            preagg_exec_times.append(float(v[6]))
            preagg_wait_times.append(float(v[7]))
        if k[0].startswith('resnet'):
            resnet_exec_times.append(float(v[6]))
            resnet_wait_times.append(float(v[7]))
        if k[0].startswith('score'):
            score_exec_times.append(float(v[6]))
            score_wait_times.append(float(v[7]))
        if k[0].startswith('storeclass'):
            storeclass_exec_times.append(float(v[6]))
            storeclass_wait_times.append(float(v[7]))

    # straggling resnet logs don't hit home. manually insert them by parsing 
    # the raw resnet8 log files
    try:
        with open(STRAGGLING_RESNET, 'r') as f:
            for line in f:
                if line.startswith('DEBUG:root:rt_enter '):
                    straggler_arriv_time = line.split()
                    straggler_arriv_time = float(straggler_arriv_time[-1])
                if line.startswith('DEBUG:root:rt_enter_task'):
                    straggler_start_time = line.split()
                    straggler_start_time = float(straggler_start_time[-1])
                    straggler_wait_time = straggler_start_time - straggler_arriv_time
                    resnet_wait_times.append(straggler_wait_time)
                if line.startswith('resnet_finish '): 
                # if line.startswith('DEBUG:root:rt_finish '): # use this if krishna's print statements aren't coming out
                    straggler_finish_time = line.split()
                    resnet_exec_time = float(straggler_finish_time[-1])  - straggler_start_time
                    resnet_exec_times.append(float(resnet_exec_time))
    except FileNotFoundError:
        print("{} does not exist".format(STRAGGLING_RESNET))

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
    if len(sys.argv) > 1:
        TEST_INDICATORS = sys.argv[1]

    COMM_TIMES = "filtered_logs/{}comm.log".format(TEST_INDICATORS)
    MAKESPAN = "filtered_logs/{}makespan.log".format(TEST_INDICATORS)
    TASK_TIMES = "filtered_logs/{}task.log".format(TEST_INDICATORS)
    STRAGGLING_RESNET = "filtered_logs/{}resnet8.log".format(TEST_INDICATORS)
    MASTER_SERVICE = "filtered_logs/{}master.log".format(TEST_INDICATORS)

    os.makedirs('figures', exist_ok=True)

    print("Graphing and calculating averages for test {}".format(TEST_INDICATORS))

    try:
        with open(TASK_TIMES, 'r') as f:
            task_log = eval(f.read())
            plot_task_timings(task_log, TEST_INDICATORS)
    except FileNotFoundError:
        print("{} does not exist".format(TASK_TIMES))

    try:
        with open(COMM_TIMES, 'r') as f:
            comm_log = eval(f.read())
            plot_comm_times(comm_log, TEST_INDICATORS)
    except FileNotFoundError:
        print("{} does not exist".format(COMM_TIMES))

    try:
        with open(MAKESPAN, 'r') as f:
            makespan_log = eval(f.read())
            plot_makespan(makespan_log, TEST_INDICATORS)
    except FileNotFoundError:
        print("{} does not exist".format(MAKESPAN))

    plt.show()