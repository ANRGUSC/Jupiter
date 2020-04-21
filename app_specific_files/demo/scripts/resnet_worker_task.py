import torch
import torchvision.models as models
import torchvision.transforms as transforms
import os
import numpy as np
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets
import shutil

def task(file_, pathin, pathout): 
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
    for f in [file_]:
        ### Read input files.
        img = Image.open(os.path.join(pathin, f))
        ### Apply transforms.
       	img_tensor = composed(img)
        ### 3D -> 4D (batch dimension = 1)
        img_tensor.unsqueeze_(0) 
        #img_tensor =  input_batch[0]
        ### call the ResNet model
        output = model(img_tensor) 
        pred = torch.argmax(output, dim=1).numpy().tolist()
        ### To simulate slow downs
        #distrib = np.load('/home/collage_inference/resnet/latency_distribution.npy')
        # s = np.random.choice(distrib)
        ### Copy to appropriate destination paths
        if pred[0] == 555: ### fire engine. class 1
            source = os.path.join(pathin, f)
            f_split = f.split("prefix_")[1]
            destination = os.path.join(pathout, "class1_prefix_" + f_split)
            out_list.append(shutil.copyfile(source, destination))
        elif pred[0] == 779: ### school bus. class 2
            source = os.path.join(pathin, f)
            f_split = f.split("prefix_")[1]
            destination = os.path.join(pathout, "class2_prefix_" + f_split)
            out_list.append(shutil.copyfile(source, destination))
        else: ### not either of the classes
            source = os.path.join(pathin, f)
            f_split = f.split("prefix_")[1]
            destination = os.path.join(pathout, "classNA_prefix_" + f_split)
            out_list.append(shutil.copyfile(source, destination))
    return out_list

if __name__ == "__main__":
    #filelist = ['outmasterprefix_n03345487_1002.JPEG', 'outmasterprefix_n04146614_10015.JPEG']
    file_ = 'outmasterprefix_n03345487_1002.JPEG'
    pathin = './to_resnet/'
    pathout = './classified_images/'
    #for f in filelist:
    task(file_, pathin, pathout)    
