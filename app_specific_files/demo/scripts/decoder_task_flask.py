### An input is the collage predictions file
### Another input is the predictions from ResNet nodes
### Figure out if any ResNet node(s) is slow, if so, move the corresponding image from Master worker task and to the corresponding store_class* task.
import os
import pickle

from multiprocessing import Process, Manager
from flask import Flask, request
import configparser
import urllib
import loggingg
import time

app = Flask(__name__)
global logging
logging.basicConfig(level = logging.DEBUG)
### NOTETOQUYNH: Set this to maximum number of ResNet tasks in the DAG
max_num_remaining_resnet_tasks = 9 
num_remaining_resnet_tasks = max_num_remaining_resnet_tasks 
working_resnet_tasks_dict = {}
### NOTETOQUYNH: Set this to master node ip/port
master_node_port = ":"

def task(filelist, pathin, pathout):
    global num_remaining_resnet_tasks
    global max_num_remaining_resnet_tasks
    global working_resnet_tasks_dict
    global master_node_port
    out_list = []
    for f in filelist:
        with open(pathin + f, "rb") as inp_file:
            preds = pickle.load(inp_file)
    ### Busy wait till a timeout to receive requests from ResNet and Collage tasks
    ### NOTETOQUYNH: This time_to_wait in seconds needs to be set depending on the system. Floating point
    ### NOTETOQUYNH: Set the time value in floating point format
    time_to_wait = 2.0
    while time_to_wait >= 0.0:
        if num_remaining_resnet_tasks == 0:
            break
        else:
            time_to_wait -= 0.5 # reduce time to wait
            time.sleep(0.5)
    # Find the missing resnet tasks
    assert(num_remaining_resnet_tasks >= 0)
    missing_resnet_tasks_set = set(range(0, max_num_remaining_resnet_tasks + 1))
    missing_resnet_tasks = []
    missing_resnet_tasks_str = ""
    class_predictions = []
    class_predictions_str = ""
    if num_remaining_resnet_tasks > 0: # Only if there are slow running resnet tasks
        missing_resnet_tasks_set = missing_resnet_tasks_set - set(working_resnet_tasks_dict.keys())
        for task in missing_resnet_tasks_set:
            task_pred = preds[task]
            if task_pred != -1:
                missing_resnet_tasks.append(str(task))
                class_predictions.append(str(task_pred))
        missing_resnet_tasks_str = " ".join(missing_resnet_tasks) 
        class_predictions_str = " ".join(class_predictions)
        # Send request to Master task
        send_requests_to_master_task(missing_resnet_tasks_str, class_predictions_str,  master_node_port)
    # Reset global variables
    working_resnet_tasks_dict = {}
    num_remaining_resnet_tasks = max_num_remaining_resnet_tasks
    # dummy output file for Jupiter 
    with open(pathout + "outdecoderprefix.txt", "w") as out_file:
        out_file.write("dummy output file")
        out_list.append(out_file)
    return out_list 

def recv_prediction_from_resnet_task():
    """
    Receive predictions from resnet tasks
     
    Raises:
        Exception: failed processing in Flask
    """
    global num_remaining_resnet_tasks
    global working_resnet_tasks_dict
    try:
        resnet_task_num = request.args.get('resnet_task_num')
        prediction = request.args.get('msg')
        working_resnet_tasks_dict[resnet_task_num] = prediction
        # If num_remaining_resnet_tasks is <= 0, something is wrong
        assert(num_remaining_resnet_tasks >= 1)
        num_remaining_resnet_tasks -= 1
    except Exception as e:
        logging.debug("Bad reception or failed processing in Flask for receiving prediction from resnet tasks")
        logging.debug(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_prediction_from_resnet_task', 'recv_prediction_from_resnet_task', recv_prediction_from_resnet_task)

def send_requests_to_master_task(missing_resnet_tasks_str, class_predictions_str,  master_node_port):
    """
    Sending missing/slow resnet tasks information to flask server on master task
    Args:
        missing_resnet_tasks: missing/slow resnet tasks
        class_predictions: class predictions for missing resnet tasks
    Returns:
        str: the message if successful, "not ok" otherwise.
    Raises:
        Exception: if sending message to flask server on master is failed
    """
    try:
        url = "http://" + master_node_port + "/recv_missing_from_decoder_task"
        params = {'missing_resnet_tasks': missing_resnet_tasks_str,'class_predictions': class_predictions_str}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        logging.debug("Sending my prediction info to flask server on master FAILED!!!")
        logging.debug(e)
        return "not ok"
    return res

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        logging.debug("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)

def main():
    ### NOTETOQUYNH - Begin
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    global FLASK_DOCKER
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
    ### NOTETOQUYNH - End

    filelist = ['outcollageprefix_collage_preds.pickle']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == "__main__":
    main()
