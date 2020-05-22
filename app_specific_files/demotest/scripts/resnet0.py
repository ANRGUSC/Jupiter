import torch
from torchvision import models
from torchvision import transforms
import os
import numpy as np
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets
import shutil
import time
import configparser

#Krishna
import urllib
import logging
from pathlib import Path

taskname = Path(__file__).stem
resnet_task_num = int(taskname.split('resnet')[1])

global logging
logging.basicConfig(level = logging.DEBUG)
global decoder_node_port
#Krishna



INI_PATH = 'jupiter_config.ini'
config = configparser.ConfigParser()
config.read(INI_PATH)

global FLASK_DOCKER, FLASK_SVC
FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
FLASK_SVC   = int(config['PORT']['FLASK_SVC'])

global all_nodes, all_nodes_ips, map_nodes_ip, master_node_port
all_nodes = os.environ["ALL_NODES"].split(":")
all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":") 
logging.debug(all_nodes)
map_nodes_ip = dict(zip(all_nodes, all_nodes_ips))
decoder_node_port = map_nodes_ip['decoder'] + ":" + str(FLASK_SVC )


def task(file_, pathin, pathout):
    global resnet_task_num
    file_ = [file_] if isinstance(file_, str) else file_ 
    ### set device to CPU
    device = torch.device("cpu")
    ### Load model
    model = models.resnet34(pretrained=True)
    model.eval()
    model.to(device)
    ### Transforms to be applied on input images
    composed = transforms.Compose([
               transforms.Resize(256, Image.ANTIALIAS),
               transforms.CenterCrop(224),
               transforms.ToTensor()])
    out_list = []

    for i, f in enumerate(file_):
        ### Read input files.
        img = Image.open(os.path.join(pathin, f))

        ### Apply transforms.
       	img_tensor = composed(img)
        ### 3D -> 4D (batch dimension = 1)
        img_tensor.unsqueeze_(0) 
        #img_tensor =  input_batch[0]
        ### call the ResNet model
        try:
            output = model(img_tensor) 
            pred = torch.argmax(output, dim=1).detach().numpy().tolist()
            ### To simulate slow downs
            #distrib = np.load('/home/collage_inference/resnet/latency_distribution.npy')
            # s = np.random.choice(distrib)
            ### Copy to appropriate destination paths
            logging.debug(os.path.join(pathin, f))
            logging.debug(pred[0])
            if pred[0] == 555: ### fire engine. class 1
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                #destination = os.path.join(pathout, "class1_" + f)
                destination = os.path.join(pathout,  "resnet" + str(resnet_task_num)+ "_storeclass1_" + f)
                # destination = os.path.join(pathout, "storeclass1_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 779: ### school bus. class 2
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass2_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 270: ### white wolf. class 3
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass3_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 276: ### hyena. class 4
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass4_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 278: ### kitfox. class 5
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass5_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 283: ### persian cat. class 6
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass6_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 288: ### leopard. class 7
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass7_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 291: ### lion. class 8
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass8_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 292: ### tiger. class 9
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass9_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 295: ### black bear. class 10
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass10_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 298: ### moongoose. class 11
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass11_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 340: ### zebra. class 12
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass12_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 341: ### hog. class 13
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass13_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 344: ### hippo. class 14
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass14_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 345: ### ox. class 15
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass15_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 346: ### buffallo. class 16
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass16_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 348: ### ram. class 17
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass17_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 352: ### impala . class 18
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass18_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 354: ### camel. class 19
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass19_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            elif pred[0] == 360: ### otter. class 20
                source = os.path.join(pathin, f)
                # f_split = f.split("prefix_")[1]
                # destination = os.path.join(pathout, "class2_" + f)
                destination = os.path.join(pathout, "resnet" + str(resnet_task_num) + "_storeclass20_"+ f)
                # destination = os.path.join(pathout, "storeclass2_" + f)
                out_list.append(shutil.copyfile(source, destination))
            else: ### not either of the classes # do nothing
                print('This does not belong to any classes!!!')
                #source = os.path.join(pathin, f)
                #destination = os.path.join(pathout, "classNA_" + f)
                #out_list.append(shutil.copyfile(source, destination))
        except Exception as e:
            logging.debug("Exception during Resnet prediction")
            logging.debug(e)

        #Krishna
        # purposely add delay time to slow down the sending
        # time.sleep(3) #>=2 
        # return [] #slow resnet node: return empty
        send_prediction_to_decoder_task(pred[0], decoder_node_port)
        #Krishna
    return out_list

#Krishna
def send_prediction_to_decoder_task(prediction, decoder_node_port):
    """
    Sending prediction and resnet node task's number to flask server on decoder
    Args:
        prediction: the prediction to be sent
    Returns:
        str: the message if successful, "not ok" otherwise.
    Raises:
        Exception: if sending message to flask server on decoder is failed
    """
    global resnet_task_num
    try:
        logging.debug('Send prediction to the decoder')
        url = "http://" + decoder_node_port + "/recv_prediction_from_resnet_task"
        ### NOTETOQUYNH: set resnet_task_num to ID of the resnet worker task (0 to 10)
        params = {'msg': prediction, "resnet_task_num": resnet_task_num}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        logging.debug("Sending my prediction info to flask server on decoder FAILED!!! - possibly running on the execution profiler")
        #logging.debug(e)
        return "not ok"
    return res
#Krishna

def main():
    #filelist = ["master_resnet0_n03345487_10.JPEG"]
    filelist = ['master_resnet0_n03345487_10.JPEG','master_resnet0_n04146614_1.JPEG','master_resnet0_n04146614_25.JPEG','master_resnet0_n04146614_27.JPEG',
       'master_resnet0_n04146614_30.JPEG','master_resnet0_n04146614_36.JPEG',
       'master_resnet0_n03345487_351.JPEG']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile

