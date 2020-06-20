## Instructions

Unzip filtered_logs.zip. Change the variables at the top of plot_log_data.py
and then simply run the script.

Sample key-value for task logs (e.g. execution times):

    ('score5b', '553imgtiger.JPEG'): [1592378580.030726, 1592378580.3423898, 1592378581.980461, '1.9497349262237549', '1.638071060180664', '0.3116638660430908', '1.0053551197052002', '0.6309590339660645', '0.31342077255249023'],

Legend for the key-values for task logs:

('task_name','local_input_file'): ['enter_time','proc_create_time','proc_exit_time',
'elapse_time','duration_time','waiting_time','service_time', 'wait_time','proc_shutdown_interval']

Definitions of the legend:

 * enter_time: time when file enters input folder at this task

 * execute_time: timestamp before a process is created to run the task() function of task_name

 * proc_exit_time: timestamp after the process that is created exits

 * elapse_time: finish_time - enter_time

 * duration_time: finish_time - execute_time (total time the process running a single task is alive)

 * waiting_time: execute_time - enter_time (time between when an input file enters and when it begins being processed)

 * service_time: time between when task() function starts (when its in the CPU context) and when the task() finishes (right before it exits)

 * wait_time: time between when the file enters a task's input folder and when the input is actually being processed by task(). also can be seen as how long it takes a process to be created

 * proc_shutdown_interval: time between when the task() function reaches the end of its code to the time when the process that calls task() successfully exits


In the code, the legend actually is the following. We have changed here to be
more readable.

'Enter_time','Execute_time','Finish_time','Elapse_time','Duration_time','Waiting_time', 'Real execution time', 'Prewaiting','Postwaiting'


