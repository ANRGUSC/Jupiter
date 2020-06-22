import os
import sys
import matplotlib.pyplot as plt
from statistics import mean

# SEE README.md for more information on naming conventions!

# these are the filenames to process, all dictated by TEST_INDICATORS
# First two binary digits indicate the test flags for coding
# Letters indicate test number (to differentiate from the flags)
# postfix "sleep" indicates if artificial sleeps are injected in the test
# examples: "11a", "01a", "01b" "01a-sleep"
TEST_INDICATORS = "11c-"
COMM_TIMES = "filtered_logs/{}comm.log".format(TEST_INDICATORS)
MAKESPAN = "filtered_logs/{}makespan.log".format(TEST_INDICATORS)
TASK_TIMES = "filtered_logs/{}task.log".format(TEST_INDICATORS)


def plot_makespan(makespan_log, file_prefix):

    makespans = []

    for k, v in makespan_log.items():
        makespans.append(v)

    fig1 = plt.figure()
    plt.plot(makespans, '.')
    plt.title("makespan vs image")
    plt.ylabel("seconds")
    fig1.savefig('figures/{}makespans.png'.format(file_prefix))


def plot_comm_times(comm_log, file_prefix):

    master_to_resnet = []
    resnet_to_storeclass = []
    storeclass_to_lccenc = []
    lccenc_to_score = []
    score_to_preagg = []
    preagg_to_lccdec = []

    source_to_dest = ['master_to_resnet', 'resnet_to_storeclass',
    'storeclass_to_lccenc', 'lccenc_to_score', 'score_to_preagg',
    'preagg_to_lccdec']

    for k, v in comm_log.items():
        if k[1].startswith('master') and k[0].startswith('resnet'):
            master_to_resnet.append(v)
        if k[1].startswith('resnet') and k[0].startswith('storeclass'):
            resnet_to_storeclass.append(v)
        if k[1].startswith('storeclass') and k[0].startswith('lccenc'):
            storeclass_to_lccenc.append(v)
        if k[1].startswith('lccenc') and k[0].startswith('score'):
            lccenc_to_score.append(v)
        if k[1].startswith('score') and k[0].startswith('preagg'):
            score_to_preagg.append(v)
        if k[1].startswith('preagg') and k[0].startswith('lccdec'):
            preagg_to_lccdec.append(v)

    for src_dst in source_to_dest:
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

    lccdec_svc_times = []
    lccdec_wait_times = []
    lccenc_svc_times = []
    lccenc_wait_times = []
    master_svc_times = []
    master_wait_times = []
    preagg_svc_times = []
    preagg_wait_times = []
    resnet_svc_times = []
    resnet_wait_times = []
    score_svc_times = []
    score_wait_times = []

    task_and_statistic = [
        ['lccdec_svc_times', 'lccdec_wait_times'],
        ['lccenc_svc_times', 'lccenc_wait_times'],
        ['master_svc_times', 'master_wait_times'], 
        ['preagg_svc_times', 'preagg_wait_times'],
        ['resnet_svc_times', 'resnet_wait_times'],
        ['score_svc_times', 'score_wait_times']
    ]  

    # keys are tuples:
    # ('task_name','local_input_file')

    # values are a list:
    # ['enter_time','proc_create_time','proc_exit_time', 'elapse_time',
    # 'duration_time','waiting_time','service_time', 'wait_time',
    # 'proc_shutdown_interval']

    for k, v in task_log.items():
        if k[0].startswith('lccdec'):
            lccdec_svc_times.append(float(v[6]))
            lccdec_wait_times.append(float(v[7]))
        if k[0].startswith('lccenc'):
            lccenc_svc_times.append(float(v[6]))
            lccenc_wait_times.append(float(v[7]))
        if k[0].startswith('master'):
            master_svc_times.append(float(v[6]))
            master_wait_times.append(float(v[7]))
        if k[0].startswith('preagg'):
            preagg_svc_times.append(float(v[6]))
            preagg_wait_times.append(float(v[7]))
        if k[0].startswith('resnet'):
            resnet_svc_times.append(float(v[6]))
            resnet_wait_times.append(float(v[7]))
        if k[0].startswith('score'):
            score_svc_times.append(float(v[6]))
            score_wait_times.append(float(v[7]))

    for task in task_and_statistic:
        fig = plt.figure()
        plt.plot(eval(task[0]), '.')
        plt.plot(eval(task[1]), 'y+')
        svc_time_avg = mean(eval(task[0]))
        print("{} average is {}s".format(task[0], svc_time_avg))
        wait_time_avg = mean(eval(task[1]))
        print("{} average is {}s".format(task[1], wait_time_avg))
        plt.title(
            "{} {} service time (.) and wait times (+) vs. job instance".format(file_prefix, task[0][0:6]) +
            "\nservice time avg = {}".format(svc_time_avg) +
            "\nwait time avg = {}".format(wait_time_avg)
        )
        plt.ylabel("seconds")
        plt.tight_layout()
        fig.savefig('figures/{}_{}_svc_times.png'.format(file_prefix, task[0][0:6]))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        TEST_INDICATORS = sys.argv[1]

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
        print("{} does not exist".format(TASK_TIMES))

    try:
        with open(MAKESPAN, 'r') as f:
            makespan_log = eval(f.read())
            plot_makespan(makespan_log, TEST_INDICATORS)
    except FileNotFoundError:
        print("{} does not exist".format(TASK_TIMES))
