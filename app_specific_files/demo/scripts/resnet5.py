import torch
from torchvision import models
from torchvision import transforms
# import torchvision.models as models
# import torchvision.transforms as transforms
import os
import numpy as np
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets
import shutil

resnet_task_num = 5

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
        print(f)
        print(os.path.join(pathin, f))
        ### Read input files.
        img = Image.open(os.path.join(pathin, f))

        ### Apply transforms.
       	img_tensor = composed(img)
        ### 3D -> 4D (batch dimension = 1)
        img_tensor.unsqueeze_(0) 
        #img_tensor =  input_batch[0]
        ### call the ResNet model
        output = model(img_tensor) 
        pred = torch.argmax(output, dim=1).detach().numpy().tolist()
        ### To simulate slow downs
        #distrib = np.load('/home/collage_inference/resnet/latency_distribution.npy')
        # s = np.random.choice(distrib)
        ### Copy to appropriate destination paths
        if pred[0] == 555: ### fire engine. class 1
            source = os.path.join(pathin, f)
            # f_split = f.split("prefix_")[1]
            #destination = os.path.join(pathout, "class1_" + f)
            destination = os.path.join(pathout, "storeclass1_" + "resnet" + str(resnet_task_num) + f)
            out_list.append(shutil.copyfile(source, destination))
        elif pred[0] == 779: ### school bus. class 2
            source = os.path.join(pathin, f)
            # f_split = f.split("prefix_")[1]
            # destination = os.path.join(pathout, "class2_" + f)
            destination = os.path.join(pathout, "storeclass2_" + "resnet" + str(resnet_task_num) + f)
            out_list.append(shutil.copyfile(source, destination))
        else: ### not either of the classes # do nothing
            print('This does not belong to any classes!!!')
            #source = os.path.join(pathin, f)
            #destination = os.path.join(pathout, "classNA_" + f)
            #out_list.append(shutil.copyfile(source, destination))
    return out_list

def main():
    filelist = ["outmaster_n03345487_10.JPEG"]
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile

# if __name__ == "__main__":
#     #filelist = ['outmasterprefix_n03345487_1002.JPEG', 'outmasterprefix_n04146614_10015.JPEG']
#     file_ = 'outmasterprefix_n03345487_1002.JPEG'
#     pathin = './to_resnet/'
#     pathout = './classified_images/'
#     #for f in filelist:
#     task(file_, pathin, pathout)    
