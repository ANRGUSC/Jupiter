input/output files naming issue (for streaming input into circe node)
the input from circe home node are called "input0, input1, ..."
for now assume each task only has one output file (but could have multiple input files from multiple parent tasks)
then output of a certain task can be called inputX_taskY, which is also the input of its children
