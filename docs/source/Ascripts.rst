Scripts Reference
=================

.. note:: This page gives an overview of all public **Scripts** which helps to build and deploy the **JUPITER** system in **Kubernetes**. 

Build scripts
-------------
.. toctree::
   :maxdepth: 4

   mulhome_scripts/build_push_circe
   mulhome_scripts/build_push_pricing_circe
   mulhome_scripts/build_push_exec
   mulhome_scripts/build_push_heft
   mulhome_scripts/build_push_jupiter
   mulhome_scripts/build_push_profiler
   mulhome_scripts/build_push_wave

Teardown scripts
----------------
.. toctree::
   :maxdepth: 4

   mulhome_scripts/delete_all_circe
   mulhome_scripts/delete_all_pricing_circe
   mulhome_scripts/delete_all_exec
   mulhome_scripts/delete_all_heft
   mulhome_scripts/delete_all_profilers
   mulhome_scripts/delete_all_waves
   mulhome_scripts/k8s_jupiter_teardown
   mulhome_scripts/auto_teardown_system

Deploy scripts
--------------
.. toctree::
   :maxdepth: 4
   
   mulhome_scripts/k8s_circe_scheduler
   mulhome_scripts/k8s_pricing_circe_scheduler
   mulhome_scripts/k8s_exec_scheduler
   mulhome_scripts/k8s_heft_scheduler
   mulhome_scripts/k8s_jupiter_deploy
   mulhome_scripts/k8s_profiler_scheduler
   mulhome_scripts/k8s_wave_scheduler
   mulhome_scripts/auto_deploy_system
   mulhome_scripts/auto_teardown_system

Configuration scripts
---------------------
.. toctree::
   :maxdepth: 4

   mulhome_scripts/write_circe_service_specs
   mulhome_scripts/write_circe_specs
   mulhome_scripts/write_pricing_circe_service_specs
   mulhome_scripts/write_pricing_circe_specs
   mulhome_scripts/write_exec_service_specs
   mulhome_scripts/write_exec_specs
   mulhome_scripts/write_heft_service_specs
   mulhome_scripts/write_heft_specs
   mulhome_scripts/write_profiler_service_specs
   mulhome_scripts/write_profiler_specs
   mulhome_scripts/write_wave_service_specs
   mulhome_scripts/write_wave_specs

Docker file preparation scripts
-------------------------------
.. toctree::
   :maxdepth: 4

   circe/original/circe_docker_files_generator
   profilers/execution_profiler_mulhome/exec_docker_files_generator
   profilers/network_resource_profiler_mulhome/profiler_docker_files_generator
   task_mapper/heft_mulhome/modified/heft_dockerfile_generator
   task_mapper/wave_mulhome/greedy_wave/wave_docker_files_generator


Other scripts
-------------
.. toctree::
   :maxdepth: 4

   mulhome_scripts/static_assignment
   mulhome_scripts/utilities
   mulhome_scripts/keep_alive

   

   
