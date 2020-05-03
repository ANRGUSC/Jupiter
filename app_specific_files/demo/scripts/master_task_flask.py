# Bunch of import statements
import os
import shutil
from PIL import Image
# import numpy as np
from multiprocessing import Process, Manager
from flask import Flask, request
import configparser
import urllib
import loggingg
import time
"""
Task for master encoder node.
1) Takes as input multiple image files and creates a collage image file. It is ideal to have 9 different inputs to create one collage image. 
2) Sends the image files to ResNet or Collage task folders downstream.
3) Flask server endpoints to receive information from decoder and send downstream to storage class nodes.
"""

app = Flask(__name__)
global logging
logging.basicConfig(level = logging.DEBUG)
### NOTETOQUYNH: Need to set the below
### store class node tasks ip/port, store class node paths
store_class_tasks_node_port_dict = {}
store_class_tasks_paths_dict = {}
### May be need to use job ids to tackle issues coming from queuing/slowdowns
tasks_to_images_dict = {}

def transfer_data_scp(destination_node_port, source_path, destination_path):
    """Transfer data using SCP
    """
    pass
    return

def recv_missing_from_decoder_task():
    """
    Receive information on slow/missing resnet tasks from the decoder task
    Forward the images to corresonding destination storage nodes
    Raises:
        Exception: failed processing in Flask
    """
    global store_class_tasks_node_port_dict
    global tasks_to_images_dict
    try:
        missing_resnet_tasks_str = request.args.get('missing_resnet_tasks')
        class_predictions_str = request.args.get('class_predictions')
        missing_resnet_tasks = missing_resnet_tasks_str.split(" ")
        class_predictions = class_predictions_str.split(" ")
        for task,cls in zip(missing_resnet_tasks, class_predictions):
            source_path = tasks_to_images_dict[task]
            destination_node_port = store_class_tasks_node_port_dict[cls]
            destination_path = store_class_tasks_paths_dict[cls]
            #if pred[0] == 555: ### fire engine. class 1
            #    f_split = f.split("prefix_")[1]
            #    destination = os.path.join(pathout, "class1_prefix_" + f_split)
            #elif pred[0] == 779: ### school bus. class 2
            #    f_split = f.split("prefix_")[1]
            #    destination = os.path.join(pathout, "class2_prefix_" + f_split)
            #else: ### not either of the classes
            #    pass
            transfer_data_scp(destination_node_port, source_path, destination_path)
    except Exception as e:
        logging.debug("Bad reception or failed processing in Flask for receiving slow resnet tasks information from decoder task")
        logging.debug(e)
        return "not ok"
    return "ok"
app.add_url_rule('/recv_missing_from_decoder_task', 'recv_missing_from_decoder_task', recv_missing_from_decoder_task)


### create a collage image and write to a file
def create_collage(input_list, collage_spatial, single_spatial, single_spatial_full, w):
    collage = Image.new('RGB', (single_spatial*w,single_spatial*w))
    collage_resized = Image.new('RGB', (collage_spatial, collage_spatial))
    ### Crop boundaries. Square shaped.
    left_crop = (single_spatial_full - single_spatial)/2
    top_crop = (single_spatial_full - single_spatial)/2
    right_crop = (single_spatial_full + single_spatial)/2
    bottom_crop = (single_spatial_full + single_spatial)/2
    for j in range(w):
        for i in range(w):
            ### NOTE: Logic for creation of collage can be modified depending on latency requirements.
            ### open -> resize -> crop
            idx = j * w + i 
            im = Image.open(input_list[idx]).resize((single_spatial_full,single_spatial_full), Image.ANTIALIAS).crop((left_crop, top_crop, right_crop, bottom_crop))
            ### insert into collage. append label.
            collage.paste(im, (int(i*single_spatial), int(j*single_spatial)))
    #collage = np.asarray(collage)
    #collage = np.transpose(collage,(2,0,1))
    #collage /= 255.0
    ### write to file 
    collage_name = "./outmasterprefix_new_collage.JPEG"
    collage_resized = collage.resize((collage_spatial, collage_spatial), Image.ANTIALIAS)
    collage_resized.save(collage_name)
    return collage_name

def helper_copyfile(f, pathin, pathout, out_list):
    source = os.path.join(pathin, f)
    print("file is", f)
    f_split = f.split("prefix_")[1]
    destination = os.path.join(pathout, "outmasterprefix_" + f_split)
    #try: 
    out_list.append(shutil.copyfile(source, destination))
    #except: 
    #print("ERROR while copying file in master_task.py")
    return

def helper_update_tasks_to_images_dict(task_num, f, pathin):
    ### Reusing the input files to the master node. NOT creating a local copy of input files.
    source = os.path.join(pathin, f)
    tasks_to_images_dict[task_num] = source 
    return

def task(filelist, pathin, pathout):
    out_list = [] # output file list. Ordered as => [collage_file, image1, image2, ...., image9]
    ### send to collage task
    ### Collage image is arranged as a rectangular grid of shape w x w 
    w = 3 
    num_images = w * w
    collage_spatial = 416
    single_spatial = 224
    single_spatial_full = 256
    input_list = []
    ### List of images that are used to create a collage image
    for i in range(num_images):
        ### Number of files in file list can be less than the number of images needed (9). Optimal value is 9.
        file_idx = int(i % len(filelist))
        input_list.append(os.path.join(pathin, filelist[file_idx]))
        # update local image files dict
        helper_update_tasks_to_images_dict(i, filelist[file_idx], pathin)
    #collage_file = create_collage(input_list, collage_spatial, single_spatial, single_spatial_full, w).astype(np.float16)
    collage_file = create_collage(input_list, collage_spatial, single_spatial, single_spatial_full, w)
    helper_copyfile(collage_file, "", pathout[0], out_list) 
    ### send to resnet tasks
    for f in filelist:
        helper_copyfile(f, pathin, pathout[1], out_list)
    return out_list 

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
    filelist = ['outds1prefix_n03345487_1002.JPEG', 'outds2prefix_n04146614_10015.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
	
if __name__ == "__main__":
    main()
