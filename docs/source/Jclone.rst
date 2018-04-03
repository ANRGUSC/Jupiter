Clone Instructions
==================

This Repository comes with a submodule with links to another repository that contains codes related to one application (Distributed Network Anomaly Detection) of Jupiter.

- If you are interested in cloning just the Jupiter Orchestrator, not the application specific files, run :

.. code-block:: bash
   :linenos:
    
    git clone git@github.com:ANRGUSC/Jupiter.git

- If you are interested in cloning the Jupiter Orchestrator along with the Distributed Network Anomaly Detection related files, run :

.. code-block:: bash
   :linenos:

    git clone --recurse-submodules git@github.com:ANRGUSC/Jupiter.git
    cd Jupiter
    git submodule update --remote