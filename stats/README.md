EXPERIMENT 8

1. Makespan log
makespan app_name app_id file_name total_makespan
Ex: makespan dummy100 dummy1001 3botnet.ipsum 358.68093729019165

2. Mapping latency log
mappinglatency pricedecoupled node_id app_id mapping_latency

2.1. Decoupled (only WAVE)
Ex: mappinglatency pricedecoupled node_id dummy1001 195.166679
2.2 Integrated
Ex: mappinglatency priceintegrated computenode9  dummy1001 0.147737
2.3 Push
Ex: mappinglatency pricepush originalheft dummy1001 15.276408 
Ex: mappinglatency pricepushc controllertask0 dummy1001 0.002630 
2.4 Event
Ex: mappinglatency priceevent originalheft dummy1001 25.539376 
Ex: mappinglatency priceevent controllertask0 dummy1001 0.002642

3. Message overhead log
msgoverhead pricedecoupled node_id msg_purpose num_msgs ....
Ex: msgoverhead pricedecoupled controllerhome assignfirst 1 

4. Power overhead log
poweroverhead node_id cpu cpu_stat memory mem_stat timestamp timestamp 
Ex: poweroverhead home cpu 0.350000 memory 9.900000 timestamp 1571839670.068319 
