# Classification and Correlation DAG (CCDAG)

Notes on how to setup the CCDAG app and run it on Jupiter.

#### app_config.yaml

* home: Receives all successfully classified and correlated images.
* nondag_tasks: Specify datasources (image producers) and their node placement
(use k8s  hostname). It's best not to list these nodes in the `node_map` section
so that Jupiter does not profile (DRUPE/Exec Prof.) or map any tasks to these
k8s nodes.
* dag_tasks: specify task name, its corresponding base script, and
its children
	. master -> resnet / collage
	. resnet -> storeclass
	. storeclass -> lccenc
	. lccenc -> score#a, score#b, score#c
	. score -> preagg
	. preagg -> lccdec
	. lccdec -> home

#### ccdag.py

Parameters for CCDAG. See comments in the file for more info.

#### resnet.py

To change the number of image classes to detect, you need to uncomment the
if-else statements in resnet.py.

#### Datasource Files

All datasource images (also serves as reference images) can be found in Drive.

https://drive.google.com/drive/u/3/folders/1tZ5QtvT5uOVVB_xzd7kPS4_x2yaXGc72

#### Additional Info
* Scripts to generate plots: generate_results.py
* List of important folders:
	- data: data images shipped to each datasource container
	- reference: reference images for coding (PART2)
	- sample_inputs: sample images for Execution Profiler
	- results: storing logs
	- figures: storing generated plots

#### How to Run Multiple CCDAG Instances

* Use a mutually exclusive list of k8s hosts under the `node_map` key
* Use a mutually exclusive set of k8s hosts for the datasource tasks
* Use a different namespace prefix for each CCDAG instance
* Generate a task mapping for each instance (you should be able to run profilers
all at once).



