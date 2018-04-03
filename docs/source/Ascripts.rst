Scripts Reference
=================

.. note:: This page gives an overview of all public **Scripts** which helps to build and deploy the **JUPITER** system in **Kubernetes**. 

Build scripts
-------------
.. toctree::
   :maxdepth: 4

   scripts/build_push_circe
   scripts/build_push_exec
   scripts/build_push_heft
   scripts/build_push_jupiter
   scripts/build_push_profiler
   scripts/build_push_wave

Teardown scripts
----------------
.. toctree::
   :maxdepth: 4

   scripts/delete_all_circe
   scripts/delete_all_exec
   scripts/delete_all_heft
   scripts/delete_all_profilers
   scripts/delete_all_waves
   scripts/k8s_jupiter_teardown

Deploy scripts
--------------
.. toctree::
   :maxdepth: 4
   
   scripts/k8s_circe_scheduler
   scripts/k8s_exec_scheduler
   scripts/k8s_heft_scheduler
   scripts/k8s_jupiter_deploy
   scripts/k8s_profiler_scheduler
   scripts/k8s_wave_scheduler

Configuration scripts
---------------------
.. toctree::
   :maxdepth: 4

   scripts/write_circe_service_specs
   scripts/write_circe_specs
   scripts/write_exec_service_specs
   scripts/write_exec_specs
   scripts/write_heft_service_specs
   scripts/write_heft_specs
   scripts/write_profiler_service_specs
   scripts/write_profiler_specs
   scripts/write_wave_service_specs
   scripts/write_wave_specs

Docker file preparation scripts
-------------------------------
.. toctree::
   :maxdepth: 4

   circe/circe_docker_files_generator
   profilers/execution_profiler/exec_docker_files_generator
   profilers/network_resource_profiler/profiler_docker_files_generator
   task_mapper/heft/heft_dockerfile_generator


Other scripts
-------------
.. toctree::
   :maxdepth: 4

   scripts/static_assignment
   scripts/utilities
   scripts/keep_alive

   

   
