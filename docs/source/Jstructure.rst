Project Structure
=================

The directory structure of the project MUST conform with the following:

.. code-block:: text

    Jupiter/
    ├── jupiter_config.py
    ├── jupiter_config.ini
    ├── k8_requirements.txt
    ├── LICENSE.txt
    ├── nodes.txt
    ├── ...
    ├── docs
    ├── circe
    │   ├── original
    |   │   ├── home_node.Dockerfile
    |   │   ├── circe_docker_files_generator.py
    |   │   ├── monitor.py
    |   │   ├── readconfig.py
    |   │   ├── requirements.txt
    |   │   ├── evaluate.py
    |   │   ├── runtime_profiler_mongodb
    |   │   ├── scheduler.py
    |   │   ├── start_home.sh
    |   │   ├── start_worker.sh
    |   │   └── worker_node.Dockerfile
    │   ├── pricing_event
    |   │   ├── home_node.Dockerfile
    |   │   ├── circe_docker_files_generator.py
    |   │   ├── monitor.py
    |   │   ├── readconfig.py
    |   │   ├── requirements.txt
    |   │   ├── evaluate.py
    |   │   ├── runtime_profiler_mongodb
    |   │   ├── scheduler.py 
    |   │   ├── compute.py 
    |   │   ├── start_home.sh
    |   │   ├── start_computing_worker.sh
    |   │   ├── start_controller_worker.sh
    |   │   ├── controller_worker_node.Dockerfile
    |   │   └── computing_worker_node.Dockerfile
    │   ├── pricing_push
    ├── task_mapper 
    │   |
    |   heft_mulhome
    |   |__original
    |   |   ├── heft.Dockerfile
    |   |   ├── heft_dockerfile_generator.py
    |   |   ├── heft_dup.py
    |   |   ├── master_heft.py
    |   |   ├── read_input_heft.py
    |   |   ├── requirements.txt
    |   |   ├── start.sh
    |   |   ├── write_input_heft.py
    |   |__modified
    |   |   ├── heft.Dockerfile
    |   |   ├── heft_dockerfile_generator.py
    |   |   ├── heft_dup.py
    |   |   ├── master_heft.py
    |   |   ├── read_input_heft.py
    |   |   ├── requirements.txt
    |   |   ├── start.sh
    |   |   ├── write_input_heft.py
    └── wave_mulhome
    │   ├── random_wave      
    |   |   ├── home
    |   |   │   ├── requirements.txt
    |   |   │   ├── master_random.py
    |   |   │   └── start.sh
    |   |   └── worker
    |   |   |   ├── child_appointment_random.py
    |   |   |   ├── requirements.txt
    |   |   |   └── start.sh
    |   |   |__ home.Dockerfile
    |   |   |__ worker.Dockerfile
    |   |   |__ wave_docker_files_generator.py
    │   ├── greedy_wave  
    |   |   ├── home
    |   |   │   ├── requirements.txt
    |   |   │   ├── master_greedy.py
    |   |   │   └── start.sh
    |   |   └── worker
    |   |   |   ├── child_appointment_greedy.py
    |   |   |   ├── requirements.txt
    |   |   |   └── start.sh
    |   |   |__ home.Dockerfile
    |   |   |__ worker.Dockerfile   
    |   |   |__ wave_docker_files_generator.py
    ├── profilers
    │   ├── network_resource_profiler_mulhome
    │   |   |___home
    │   |   |   |
    |   │   │   ├── central_input
    |   │   │   │   ├── link_list.txt
    |   │   │   │   └── nodes.txt
    |   │   │   ├── central_mongod
    |   │   │   ├── central_query_statistics.py
    |   │   │   ├── central_scheduler.py
    |   │   │   ├── generate_link_list.py
    |   │   │   ├── requirements.txt
    |   │   │   ├── resource_profiling_files
    |   │   │   │   ├── insert_to_container.py
    |   │   │   │   ├── ip_path
    |   │   │   │   ├── job.py
    |   │   │   │   └── read_info.py
    |   │   │   └── start.sh
    │   |___|___worker
    |   |   |   |
    │   |   |   ├── automate_droplet.py
    │   |   |   ├── droplet_generate_random_files
    │   |   |   ├── droplet_mongod
    │   |   |   ├── droplet_scp_time_transfer
    │   |   |   ├── requirements.txt
    │   |   |   ├── resource_profiler.py
    │   |   |   └── start.sh
    |   |   |___profiler_docker_files_generator.py
    |   |   |___profiler_home.Dockerfile
    |   |   |___profiler_worker.Dockerfile
    │   ├── execution_profiler_mulhome
    │   |   |___exec_docker_files_generator.py
    │   |   |___exec_home.Dockerfile
    │   |   |___exec_worker.Dockerfile 
    │   |   |___get_files.py
    │   |   |___profiler_home.py
    │   |   |___profiler_worker.py
    │   |   |___requirements.txt
    │   |   |___start_home.sh
    │   |   |___start_worker.sh
    ├── task_specific_files
    │   └── APP_Folder
    │       ├── configuration.txt
    │       ├── app_config.ini
    │       ├── name_convert.txt 
    │       ├── sample_input
    │       │   ├── sample1
    │       │   └── sample2
    │       └── scripts
    │           ├── task1.py
    │           └── task2.py
    |
    └── mulhome_scripts
        ├── auto_deploy_system.py
        ├── auto_teardown_system.py
        ├── build_push_circe.py
        ├── build_push_pricing_circe.py
        ├── build_push_jupiter.py
        ├── build_push_profiler.py
        ├── build_push_wave.py
        ├── build_push_heft.py
        ├── build_push_exec.py
        ├── delete_all_circe.py
        ├── delete_all_pricing_circe.py
        ├── delete_all_profilers.py
        ├── delete_all_waves.py
        ├── delete_all_heft.py
        ├── delete_all_exec.py
        ├── k8s_circe_scheduler.py
        ├── k8s_pricing_circe_scheduler.py
        ├── k8s_heft_scheduler.py
        ├── k8s_exec_scheduler.py
        ├── k8s_profiler_scheduler.py
        ├── k8s_wave_scheduler.py
        ├── static_assignment.py
        ├── utilities.py
        ├── keep_alive.py
        ├── write_circe_service_specs.py
        ├── write_circe_specs.py
        ├── write_pricing_circe_service_specs.py
        ├── write_pricing_circe_specs.py
        ├── write_profiler_service_specs.py
        ├── write_profiler_specs.py
        ├── write_wave_service_specs.py
        ├── write_wave_specs.py
        ├── write_heft_service_specs.py
        ├── write_heft_specs.py
        ├── write_wave_service_specs.py
        └── write_wave_specs.py



