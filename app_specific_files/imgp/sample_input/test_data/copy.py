import os
from PIL import Image  
import PIL  

i = 0
while i < 94:
    f = Image.open(r"input1_left.jpeg")
    output_files = "input%s_left.jpeg" % (str(i+4))
    f.save(output_files)
    f.close()

    f = Image.open(r"input1_right.jpeg")
    output_files = "input%s_right.jpeg" % (str(i+4))
    f.save(output_files)
    f.close()

    i += 1
    f = Image.open(r"input2_left.jpeg")
    output_files = "input%s_left.jpeg" % (str(i+4))
    f.save(output_files)
    f.close()

    f = Image.open(r"input2_right.jpeg")
    output_files = "input%s_right.jpeg" % (str(i+4))
    f.save(output_files)
    f.close()

    i += 1
    f = Image.open(r"input3_left.jpeg")
    output_files = "input%s_left.jpeg" % (str(i+4))
    f.save(output_files)
    f.close()

    f = Image.open(r"input3_right.jpeg")
    output_files = "input%s_right.jpeg" % (str(i+4))
    f.save(output_files)
    f.close()
