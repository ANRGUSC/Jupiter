# Multi-Camera Processing DAG
Image stitching and object detection application customized for Jupiter Orchestrator (available here: https://github.com/ANRGUSC/Jupiter).



# Image Stitching and Object Detection: Task Graph
The application task graph, shown below, is intended for dispersed computing.

<div align=center><img width="600" height="600" src="https://github.com/ANRGUSC/Jupiter_image_stiching_app/blob/master/DAG.jpg"/></div>



## Generating the input files
Single input file, two street view images, is given in a repository.


## Code Structure
Jupiter accepts pipelined computations described in a form of a Graph where the main task flow is represented as a Directed Acyclic Graph(DAG). 
Thus, one should be able separate the graph into two pieces, **the DAG part and non-DAG part**.
Jupiter requires that each task in the DAG part of the graph to be written as a Python function in a separate file under the `scripts` folder. 
On the other hand the non-DAG tasks can be either Python function or a shell script with any number of arguments, located under the `scripts` folder.
The folder structure is:
```
├── configuration.txt
├── DAG.jpg
├── input_node.txt
├── LICENSE.txt
├── README.md
├── sample_input
│   ├── camera1_20190222.jpeg
│   └── camera2_20190222.jpeg
└── scripts
    ├── preprocess1.py
    ├── preprocess2.py
    ├── stitch.py
    ├── human_detection.py
    ├── config.json
    └── car_detection
        ├── cars.xml
        └── car_detection.py
```

## `sample_input` 
This folder is required according to the Jupiter guidelines as well as for testing.
One can leave it as an empty directory.

## `config.json`
According to Jupiter guideline, there MUST be a config.json file with an
entry called `taskname_map` to designate the DAG part and non DAG part of the task graph.
In this, each entry is represented as follows:
 ```
 <task_name> <task_file> <DAG_flag>  <Arguments>
 ``` 


`<task_name>` is the name of the dag task such as `simpledetector0`.

`<task_file>` is the name of the file to be run internally

`<DAG_flag`> represents whether the task is part of the DAG. If yes, set it to be `True` otherwise set it to be `False`.

`<Arguments>` represents the arguments for the tasks that are not part of the DAG portion of the task-graph.


## `configuration.txt`
To conform with Jupiter guidelines, there MUST be a `configuration.txt` file representing the graph. 
Each line of the file represents the children of each node. 
To prepare the configuration file, first the task graph needs to be converted
to an arbitrary directed graph. 
It can be done by running a Breadth First Search (BFS) type algorithm. 
Then you get a graph something like: 

<div align=center><img width="600" height="600" src="https://github.com/ANRGUSC/Jupiter_image_stiching_app/blob/master/DAG.jpg"/></div>


Now each of the non-leaf nodes and the leaf nodes that are part of original DAG
part are represented in the configuration files as 
 ```
 <node-name>  <number for inputs required> <Flag stating whether to wait for all the inputs> <child1-name>  <child2-name> ....
 ```
For all the other nodes (i.e,  leaf nodes that are not part of the original DAG portion) such as `DFTslave00` represent them as 
 ```
 <node-name>    1       False   <node-name> 
 ```


## `input_node.txt`
This file is required by the WAVE scheduler. This basically initiates the WAVE
scheduler's random mapping. 
This file includes random mapping for the tasks that has no parent.

## `script`
This folder contains all the executables related to the task graph.

### `preprocess<SPLIT_ID>.py`
SPLIT_ID (0 or 1, in our case) uniquely idenfifies the input image id. This script completes some preprocessing tasks, such as converting to the gray scale.

### `stitch.py`
An implementation of image stitching algorithm.

### `human_detection.py`
Find the human targets in the stitched image. Use two preprocessed images as inputs.

### `car_detection/car_detection.py`
Find the car targets in the stitched image.

### `car_detection/cars.xml`
A trained classifier used to detecion cars.
 

## Execution
This code is customized to be executed with Jupiter Only. 

# References

[1] [Python Multiple Image Stitching](https://github.com/kushalvyas/Python-Multiple-Image-Stitching)

[2] [Car Detection with Opencv](http://www.technicdynamic.com/2017/08/28/python-motion-detection-with-opencv-simple/)


# Acknowledgment
This material is based upon work supported by Defense Advanced Research Projects Agency (DARPA) under Contract No. HR001117C0053. Any views, opinions, and/or findings expressed are those of the author(s) and should not be interpreted as representing the official views or policies of the Department of Defense or the U.S. Government.
