import os
import sys
import matplotlib.pyplot as plt

# SEE README.md for more information on naming conventions!

# these are the filenames to process, all dictated by TEST_INDICATORS
# First two binary digits indicate the test flags for coding
# Letters indicate test number (to differentiate from the flags)
# postfix "sleep" indicates if artificial sleeps are injected in the test
# examples: "11a", "01a", "01b" "01a-sleep"
TEST_INDICATORS = "01a-sleep"
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

    fig1.savefig('figures/makespans{}.png'.format(file_prefix))


def plot_comm_times(comm_log, file_prefix):

    master_to_resnet = []
    resnet_to_storeclass = []
    storeclass_to_lccenc = []
    lccenc_to_score = []
    score_to_preagg = []
    preagg_to_lccdec = []

    for k, v in comm_log.items():
        if k[1].startswith('master') and k[2].startswith('resnet'):
            master_to_resnet.append(v)
        if k[1].startswith('resnet') and k[2].startswith('storeclass'):
            resnet_to_storeclass.append(v)
        if k[1].startswith('storeclass') and k[2].startswith('lccenc'):
            storeclass_to_lccenc.append(v)
        if k[1].startswith('lccenc') and k[2].startswith('score'):
            lccenc_to_score.append(v)
        if k[1].startswith('score') and k[2].startswith('preagg'):
            score_to_preagg.append(v)
        if k[1].startswith('preagg') and k[2].startswith('lccdec'):
            preagg_to_lccdec.append(v)

    fig1 = plt.figure()
    plt.plot(master_to_resnet, '.')
    plt.title("master_to_resnet communication time vs job")
    fig2 = plt.figure()
    plt.plot(resnet_to_storeclass, '.')
    plt.title("resnet_to_storeclass communication time vs job")
    fig3 = plt.figure()
    plt.plot(storeclass_to_lccenc, '.')
    plt.title("storeclass_to_lccenc communication time vs job")
    fig4 = plt.figure()
    plt.plot(lccenc_to_score, '.')
    plt.title("lccenc_to_score communication time vs job")
    fig5 = plt.figure()
    plt.plot(score_to_preagg, '.')
    plt.title("score_to_preagg communication time vs job")
    fig6 = plt.figure()
    plt.plot(preagg_to_lccdec, '.')
    plt.title("preagg_to_lccdec communication time vs job")

    fig1.savefig('figures/{}_master_to_resnet_comm_times.png'.format(file_prefix))
    fig2.savefig('figures/{}_resnet_to_storeclass_comm_times.png'.format(file_prefix))
    fig3.savefig('figures/{}_storeclass_to_lccenc_comm_times.png'.format(file_prefix))
    fig4.savefig('figures/{}_lccenc_to_score_comm_times.png'.format(file_prefix))
    fig5.savefig('figures/{}_score_to_preagg_comm_times.png'.format(file_prefix))
    fig6.savefig('figures/{}_preagg_to_lccdec_comm_times.png'.format(file_prefix))


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

    fig1 = plt.figure()
    plt.plot(lccdec_svc_times, '.')
    plt.plot(lccdec_wait_times, 'y+')
    plt.title("lccdec service time (.) and wait times (+) vs. job instance")

    fig2 = plt.figure()
    plt.plot(lccenc_svc_times, '.')
    plt.plot(lccenc_wait_times, 'y+')
    plt.title("lccenc service time (.) and wait times (+) vs. job instance")

    fig3 = plt.figure()
    plt.plot(master_svc_times, '.')
    plt.plot(master_wait_times, 'y+')
    plt.title("master service time (.) and wait times (+) vs. job instance")

    fig4 = plt.figure()
    plt.plot(preagg_svc_times, '.')
    plt.plot(preagg_wait_times, 'y+')
    plt.title("preagg service time (.) and wait times (+) vs. job instance")

    fig5 = plt.figure()
    plt.plot(resnet_svc_times, '.')
    plt.plot(resnet_wait_times, 'y+')
    plt.title("resnet service time (.) and wait times (+) vs. job instance")

    fig6 = plt.figure()
    plt.plot(score_svc_times, '.')
    plt.plot(score_wait_times, 'y+')
    plt.title("score service time (.) and wait times (+) vs. job instance")

    # uncomment to save to files
    fig1.savefig('figures/{}_lccdec_svc_times.png'.format(file_prefix))
    fig2.savefig('figures/{}_lccenc_svc_times.png'.format(file_prefix))
    fig3.savefig('figures/{}_master_svc_times.png'.format(file_prefix))
    fig4.savefig('figures/{}_preagg_svc_times.png'.format(file_prefix))
    fig5.savefig('figures/{}_resnet_svc_times.png'.format(file_prefix))
    fig6.savefig('figures/{}_score_svc_times.png'.format(file_prefix))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        TEST_INDICATORS = sys.argv[1]

    os.makedirs('figures', exist_ok=True)

    with open(TASK_TIMES, 'r') as f:
        task_log = eval(f.read())
        plot_task_timings(task_log, TEST_INDICATORS)

    with open(COMM_TIMES, 'r') as f:
        comm_log = eval(f.read())
        plot_comm_times(comm_log, TEST_INDICATORS)

    with open(MAKESPAN, 'r') as f:
        makespan_log = eval(f.read())
        plot_makespan(makespan_log, TEST_INDICATORS)
