Steps to duplicate

1. Modify app_config.yaml
2. Generat configuration files: python configure_app.py tools/duplicate/demotest 
3. Fix resnet0, master for new datasources ; fix storeclass (execution profiler) for new datasources (done)
   Generate corresponding scripts: python3 duplicate_demo.py
4. Make resnet0 slow
5. Rebuild with datasources folder in push_stream (put data folder in simulation/demo_multiple_sources)
