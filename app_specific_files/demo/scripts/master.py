# Bunch of import statements
import os
import shutil
from PIL import Image
# import numpy as np
"""
Task for master encoder node.
1) Takes as input multiple image files and creates a collage image file. It is ideal to have 9 different inputs to create one collage image. 
2) Sends the image files to ResNet or Collage task folders downstream.
"""
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
    collage_name = "new_collage.JPEG"
    collage_resized = collage.resize((collage_spatial, collage_spatial), Image.ANTIALIAS)
    collage_resized.save(collage_name)
    return collage_name


def task(filelist, pathin, pathout):
    out_list = []# output file list. Ordered as => [collage_file, image1, image2, ...., image9]
    ### send to collage task
    ### Collage image is arranged as a rectangular grid of shape w x w 
    w = 3 
    num_images = w * w
    collage_spatial = 416
    single_spatial = 224
    single_spatial_full = 256
    input_list = []
    ### List of images that are used to create a collage image
    print('------')
    print(num_images)
    print(filelist)
    if not isinstance(filelist, list):
        filelist = [filelist]    

    for i in range(num_images):
        ### Number of files in file list can be less than the number of images needed (9)
        file_idx = int(i % len(filelist))
        input_list.append(os.path.join(pathin, filelist[file_idx]))
    #collage_file = create_collage(input_list, collage_spatial, single_spatial, single_spatial_full, w).astype(np.float16)

    print('Input list file')
    print(input_list)
    collage_file = create_collage(input_list, collage_spatial, single_spatial, single_spatial_full, w)
    
    shutil.copyfile(collage_file, os.path.join(pathout,"outmaster_"+collage_file))
    ### send to collage task
    outlist = ["outmaster_"+collage_file]
    ### send to resnet tasks
    for f in filelist:
        shutil.copyfile(os.path.join(pathin,f), os.path.join(pathout,"outmaster_"+f))	
        outlist.append(os.path.join(pathout,"outmaster_"+f))
    return out_list 

def main():
    filelist = ['n03345487_1002.JPEG']#n04146614_10015.JPEG
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile
	
# if __name__ == "__main__":
#     filelist = ['outds1prefix_n03345487_1002.JPEG', 'outds2prefix_n04146614_10015.JPEG']
#     pathout = ["./to_collage/", "./to_resnet/"]
#     task(filelist, "./to_master/", pathout)
