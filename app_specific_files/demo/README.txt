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

#### Datasource Files

All datasource images (also serves as reference images) can be found in Drive.

https://drive.google.com/drive/u/3/folders/1tZ5QtvT5uOVVB_xzd7kPS4_x2yaXGc72

For each datasource task you indicate on `app_config.yaml`, you must create a
custom folder under `data/`. For example, there needs to be a `data/datasource4`
folder if you have a 4th datasource task. You also need to prepend the filename
of each image under these directories with `home_master_` so that CIRCE will
know to send these images to the master service task (`source_dest_`).

There are parameters in `ccdag.py` to modify the behaviors of datasource tasks.

#### Additional Info
* Scripts to generate plots: generate_results.py
	- There are a **lot** of hardcoded pieces in here. For each CCDAG setup,
	manual modifications will be needed.
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



