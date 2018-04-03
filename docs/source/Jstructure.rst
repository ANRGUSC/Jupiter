Project Structure
=================

The directory structure of the project MUST conform with the following:

.. code-block:: text

    Jupiter/
    ├── jupiter_config.py
    ├── k8_requirements.txt
    ├── LICENSE.txt
    ├── nodes.txt
    ├── ...
    |
    ├── circe
    │   ├── home_node.Dockerfile
    │   ├── monitor.py
    │   ├── readconfig.py
    │   ├── requirements.txt
    │   ├── rt_profiler_data_update.py
    │   ├── rt_profiler_update_mongo.py
    │   ├── runSQuery.py
    │   ├── runtime_profiler_mongodb
    │   ├── scheduler.py
    │   ├── start_home.sh
    │   ├── start_worker.sh
    │   └── worker_node.Dockerfile
    |
    └── wave
    |   ├── home
    |   │   ├── Dockerfile
    |   │   ├── input_node.txt
    |   │   ├── master.py
    |   │   └── start.sh
    |   └── worker
    |       ├── child_appointment.py
    |       ├── Dockerfile
    |       ├── requirements.txt
    |       └── start.sh
    |
    ├── profilers
    │   ├── central
    │   │   ├── central_input
    │   │   │   ├── link_list.txt
    │   │   │   └── nodes.txt
    │   │   ├── central_mongod
    │   │   ├── central_query_statistics.py
    │   │   ├── central_scheduler.py
    │   │   ├── Dockerfile
    │   │   ├── generate_link_list.py
    │   │   ├── requirements.txt
    │   │   ├── resource_profiling_files
    │   │   │   ├── insert_to_container.py
    │   │   │   ├── ip_path
    │   │   │   ├── job.py
    │   │   │   └── read_info.py
    │   │   └── start.sh
    │   └── droplet
    │       ├── automate_droplet.py
    │       ├── Dockerfile
    │       ├── droplet_generate_random_files
    │       ├── droplet_mongod
    │       ├── droplet_scp_time_transfer
    │       ├── requirements.txt
    │       ├── resource_profiler.py
    │       └── start.sh
    |
    ├── task_specific_files
    │   └── APP_Folder
    │       ├── configuration.txt
    │       ├── DAG_Scheduler.txt
    │       ├── sample_input
    │       │   ├── sample1
    │       │   └── sample2
    │       └── scripts
    │           ├── task1.py
    │           └── task2.py
    |
    └── scripts
        ├── build_push_circe.py
        ├── build_push_jupiter.py
        ├── build_push_profiler.py
        ├── build_push_wave.py
        ├── delete_all_circe_deployments.py
        ├── delete_all_profilers.py
        ├── delete_all_waves.py
        ├── k8s_circe_scheduler.py
        ├── k8s_jupiter_deploy.py
        ├── k8s_jupiter_teardown.py
        ├── k8s_profiler_scheduler.py
        ├── k8s_wave_scheduler.py
        ├── static_assignment.py
        ├── write_deployment_specs.py
        ├── write_home_specs.py
        ├── write_profiler_service_specs.py
        ├── write_profiler_specs.py
        ├── write_service_specs.py
        ├── write_wave_service_specs.py
        └── write_wave_specs.py

