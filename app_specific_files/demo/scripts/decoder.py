### An input is the collage predictions file
### Another input is the predictions from ResNet nodes
### Figure out if any ResNet node(s) is slow, if so, move the corresponding image from Master worker task and to the corresponding store_class* task.
import os
import pickle

def task(filelist, pathin, pathout):
    out_list = []
    for f in filelist:
        with open(pathin + f, "rb") as inp_file:
            preds = pickle.load(inp_file)
    out_name = pathout + "outdecoder.txt"
    with open(out_name, "w") as out_file:
        out_file.write("place holder")
        out_list.append(out_name)
    return out_list 

def main():
    filelist = ['outcollage_collage_preds.pickle']
    outpath = os.path.join(os.path.dirname(__file__), 'sample_input/')
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == "__main__":
    main()