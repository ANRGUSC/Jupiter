*** Instructions on running the CCDAG application:

** Configurations  for CCDAG are specified in 2 input files :

* app_config.yaml: 
- namespace_prefix
- docker_registry
- node_map:  list of nodes in the cluster
- application:
	+ home: receive all the final output files
	+ nondag_tasks: specify datasources (images) and their locations
	+ dag_tasks: specify task name, its corresponding base script, and its children
	. master -> resnet / collage
	. resnet -> storeclass
	. storeclass -> lccenc
	. lccenc -> score#a, score#b, score#c
	. score -> preagg
	. preagg -> lccdec 
	. lccdec -> home
* ccdag.py
- JUPITER_CONFIG_INI_PATH: 
	+ '/jupiter/build/jupiter_config.ini' : docker option
	+ '../../jupiter_config.ini' : local option

- CODING_PART1: 1 to set coding option for PART1, 0 otherwise
- RESNETS_THRESHOLD: >=2 to set coding option for PART1 to 0, 1 otherwise (must combined with CODING_PART1). If RESNETS_THRESHOLD is 4, then at least (9 - 4) + 1 = 6 Resnets should respond to the flask server. Flask server will wait for at least 6 resnet responses. So, if RESNETS_THRESHOLD = 6, then at least 4 responses.

- CODING_PART2: 1 to set coding option for PART2, 0 otherwise

- EXP_NAME: experiment name (used by generate_results.py)
- EXP_ID: experiment id (used by generate_results.py)
- SLEEP_TIME: sleeping time for straggler nodes (resnet8 is the straggler when coding is set for PART1)
- MASTER_POLL_INTERVAL: Master service polls very MASTER_POLL interval
- RESNET_POLL_INTERVAL: Resnet service polls every RESNET_POLL interval
- MASTER_TO_RESNET_TIME: Master waits for this amount of time on resnets/collage tasks, before finding and forwarding the slow resnet's missing images. 
- STRAGGLER_THRESHOLD:  If this value > 1, then no stragglers are injected, 0 otherwise
- STREAM_INTERVAL: time interval sending images from datasource to master task
- NUM_IMAGES: number of images per datasource
- NUM_CLASS: number of datasources
- classlist: constant labels for image datasources


** Datasources: https://drive.google.com/drive/u/3/folders/1tZ5QtvT5uOVVB_xzd7kPS4_x2yaXGc72
** Scripts to generate plots: generate_results.py
** List of important folders:
- Data: data images 
- Reference: reference images for coding (PART2)
- Sample_inputs: sample images for Execution Profiler
- Results: storing logs
- Figures: storing generated plots