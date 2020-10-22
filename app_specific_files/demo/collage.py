import os
import shutil
import sys
import queue
import threading
import logging
import glob
import time
import json


logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


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
#task library import
import torch
from torchvision import transforms
import numpy as np
import math
from PIL import Image
from darknet_models import Darknet
from ccdag_utils import *
import configparser
global circe_home_ip, circe_home_ip_port

# Jupiter executes task scripts from many contexts. Instead of relative paths
# in your code, reference your entire app directory using your base script's
# location.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Parse app_config.yaml. Keep as a global to use in your app code.
app_config = app_config_parser.AppConfig(APP_DIR)

# Run by dispatcher (e.g. CIRCE). Use task_name to differentiate the tasks by
# name to reuse one base task file.


#task config information

config = configparser.ConfigParser()
config.read(ccdag.JUPITER_CONFIG_INI_PATH)
global FLASK_DOCKER, FLASK_SVC
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])
global global_info_ip, global_info_ip_port




def calculate_iou(L1, R1, T1, B1, L2, R2, T2, B2):
    L = max(L1, L2)
    R = min(R1, R2)
    T = max(T1, T2)
    B = min(B1, B2)
    i = max(0, R-L+1) * max(0, B-T+1) #max(0,) covers the case where no intersection exists. Why +1 I am not sure
    A1 = (R1-L1+1) * (B1-T1+1)
    A2 = (R2-L2+1) * (B2-T2+1)
    iou = i*1.0/(A1 + A2 - i)
    return iou

def calculate_pos(left, right, top, bottom, w, spatial):
    # return box in pos with maximum iou.
    pos_dict = {}
    for i in range(0,w):
        pos_dict[i] = [0]*w
        for j in range(0,w):
            pos_dict[i][j] = i + w*j
    max_iou = 0.0
    for i in range(w):
        t = i*spatial
        b = ((i+1)*spatial) - 1
        for j in range(w):
             l = j*spatial
             r = ((j+1)*spatial) - 1
             temp = calculate_iou(left, right, top, bottom, l, r, t, b)
             if max_iou < temp:
                 max_iou = temp
                 x = j
                 y = i
    #print(left, right, top, bottom, x, y)
    return (pos_dict[x])[y]

def process_collage(pred, nms_thres, conf_thres, classes_list, w, single_spatial):
    #print("pred1: ", pred.shape)
    pred = pred[pred[:, :, 4] > conf_thres]
    #print("pred2: ", pred.shape)
    if len(pred) > 0:
        detections_list = non_max_suppression(pred.unsqueeze(0), conf_thres, nms_thres)
        detections = detections_list[0]
        #print(len(detections_list))
        #print(detections.shape)
    # Draw bounding boxes and labels of detections
    if detections is not None:
        # write results to .txt file
        #results_txt_path = output_dir + "/" + 'collage_preds.txt'
        #if os.path.isfile(results_txt_path):
        #    os.remove(results_txt_path)
        #print("detections info as follows:")
        #print(detections)
        predictions_prob_list = [-1]*w*w
        predictions_list = [-1]*w*w
        for x1, y1, x2, y2, conf, cls_conf, cls_pred in detections:
            #if save_txt:
            #    with open(results_txt_path, 'a') as file:
            #        file.write(('%g %g %g %g %g %g \n') % (x1, y1, x2, y2, cls_pred, cls_conf * conf))
            pos = calculate_pos(x1, x2, y1, y2, w, single_spatial)
            prob = cls_conf * conf
            cls_pred = int(cls_pred.item())
            #print("position and probability are: ", pos, prob)
            if predictions_prob_list[pos] != -1:
                if predictions_prob_list[pos] < prob:
                    predictions_list[pos] = cls_pred
            else:
                predictions_list[pos] = cls_pred
                predictions_prob_list[pos] = prob
    #print("predictions_list is: ", predictions_list)
    #predictions_arr = np.array(predictions_list)
    predictions_list = classes_list[predictions_list].tolist()
    return predictions_list

def send_prediction_to_decoder_task(job_id, final_preds, global_info_ip_port):
    try:
        hdr = {
                'Content-Type': 'application/json',
                'Authorization': None #not using HTTP secure
                                        }
        logging.debug('Send prediction to the decoder')
        url = "http://" + global_info_ip_port + "/post-predictions-collage"
        logging.debug(url)
        params = {"job_id": job_id, 'msg': final_preds}
        response = requests.post(url, headers = hdr, data = json.dumps(params))
        logging.debug(response)
        ret_job_id = response.json()
        logging.debug(ret_job_id)
    except Exception as e:
        logging.debug("Sending my prediction info to flask server on decoder FAILED!!! - possibly running on the execution profiler")
        logging.debug(e)
        return "not ok"
    return "ok"

def task(q, pathin, pathout, task_name):

    while True:
        if q.qsize()>0:
            input_file = q.get()
            start = time.time()

            src_task, this_task, base_fname = input_file.split("_", maxsplit=3)
            log.debug(f"{task_name}: file rcvd from {src_task} : {base_fname}")

            # Process the file (this example just passes along the file as-is)
            # Once a file is copied to the `pathout` folder, CIRCE will inspect the
            # filename and pass the file to the next task.
            src = os.path.join(pathin, input_file)
            # COLLAGE CODE
            img_size=416
            w = 3
            single_spatial = math.ceil(img_size*1.0/w)
            nms_thres = 0.45
            conf_thres = 0.3
            # Load collage model
            device = torch.device("cpu")
            net_config_path = os.path.join(os.path.dirname(__file__),"yolov3-tiny.cfg")
            model = Darknet(net_config_path, img_size)
            weights_file_path = os.path.join(os.path.dirname(__file__),"best.pt")
            checkpoint = torch.load(weights_file_path, map_location="cpu")
            model.load_state_dict(checkpoint['model'])
            del checkpoint
            model.to(device).eval()
            classes_list = np.load(os.path.join(os.path.dirname(__file__),"classes_list_103_classes.npy"))
            classes_list = np.sort(classes_list)
            ### Load collage image
            composed = transforms.Compose([
                       transforms.ToTensor()])
            ### Read input files.
            collage_img = Image.open(src)
            ### Transform to tensor format.
            collage_tensor = composed(collage_img)
            ### 3D -> 4D (batch dimension = 1)
            collage_tensor.unsqueeze_(0)
            ### Classify the image
            pred = model(collage_tensor)
            ### Process predictions to get a list of final predictions
            final_preds = process_collage(pred, nms_thres, conf_thres, classes_list, w, single_spatial)
        ### Write predictions to a file and send it to decoder task's folder
            job_id = int(input_file.split("jobid")[1])
            try:
                global_info_ip = retrieve_globalinfo(os.environ['CIRCE_NONDAG_TASK_TO_IP'])
                global_info_ip_port = global_info_ip + ":" + str(FLASK_SVC)
                if ccdag.CODING_PART1:
                    send_prediction_to_decoder_task(job_id, final_preds, global_info_ip_port)
            except Exception as e:
                log.warning('Possibly running on the execution profiler: ', e)

            # read the generate output
            # based on that determine sleep and number of bytes in output file

            end = time.time()
            runtime_stat = {
                "task_name" : task_name,
                "start" : start,
                "end" : end
            }
            log.info(json.dumps(runtime_stat))

            q.task_done()
        else:
            log.debug('Not enough files')
            time.sleep(1)

    log.error("ERROR: should never reach this")


# Run by execution profiler
def profile_execution(task_name):
    q = queue.Queue()
    input_dir = f"{APP_DIR}/sample_inputs/"
    output_dir = f"{APP_DIR}/sample_outputs/"

    os.makedirs(output_dir, exist_ok=True)
    t = threading.Thread(target=task, args=(q, input_dir, output_dir, task_name))
    t.start()

    for file in os.listdir(input_dir):
        try:
            src_task, dst_task, base_fname = file.split("_", maxsplit=3)
        except ValueError:
            # file is not in the correct format
            continue

        if dst_task.startswith(task_name):
            q.put(file)
    q.join()


    # execution profiler needs the name of ouput files to analyze sizes
    output_files = []
    for file in os.listdir(output_dir):
        if file.startswith(task_name):
            output_files.append(file)

    return output_dir, output_files


if __name__ == '__main__':
    # Testing Only
    log.info("Threads will run indefintely. Hit Ctrl+c to stop.")
    for dag_task in app_config.get_dag_tasks():
        if dag_task['base_script'] == __file__:
            log.debug(profile_execution(dag_task['name']))