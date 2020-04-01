### Known Problems

 * The materialization engine seems to not pick up jobs in the queue. It may
   take minutes to hours to materialize a realization. Send messages to the
   DCOMP Slack to get this done faster.

### Prepare experiment on MergeTB (aka DCOMP Testbed)

First, prepare your cloud nodes via an "experiment" in MergeTB. Login to 
https://launch.mergetb.net, create a project, and create an experiment. To run 
the scripts in this repository, you can use the provided model mergetb_model.py.
In the Models section, upload mergetb_model.py. Then, click on the new model and 
click on "Push to Experiment". Select the experiment that you created.  If you 
used the example model, three nodes in total will be created with the hostnames
`master`, `n1`, and `n2`. 

You will access your experiment nodes through the xdc (experiment development
container?). Create an xdc container and click the link to the xdc UI. Under the
"Files" tab, you will see a drop down menu labeled "New". Expand the menu and 
click "Terminal". 

### Generate keys for your xdc

To easily SSH into all nodes in a "realization", you will need to setup keys 
using your xdc. If you decide to create new xdc's, you will need to repeat this
process.

In the xdc terminal, create an ssh key by executing `ssh-keygen`. The default
public key can be found in `~/.ssh/id_rsa.pub`. On launch.mergetb.net, go to
the "User Profiles" page. On the right side, add a key and upload the public
key file (i.e., id_rsa.pub).

### Attach xdc to experiment and materalize a realization

In MergeTB, it is our understanding that "experiment" is envisioned to be a 
what is more popularly known as a "project" in other testing platforms. A 
realization would be an instance of an experiment where each realization has
a completely separate set of compute nodes for experimentation. Materializing a
realization is simply turning on the realization instance. `{PROJECT_NAME}` and 
`{EXPERIMENT_NAME}` refer to the names used above in section "Prepare Experiment 
on MergeTB". `{REALIZATION_NAME}` is the new name for the realization (e.g. 
real0).

    mergetb login {USERNAME}
    mergetb -p {PROJECT_NAME} realize {EXPERIMENT_NAME} {REALIZATION_NAME} --accept
    mergetb -p {PROJECT_NAME} materialize {EXPERIMENT_NAME} {REALIZATION_NAME}
    attach {PROJECT_NAME} {EXPERIMENT_NAME} {REALIZATION_NAME}

If you hare having problems, `detach` and then `attach` again.

### Install prerequisites and clone repo

In your xdc, execute

    sudo apt update
    sudo apt upgrade -y

Then,

    sudo apt install git -y
    git clone https://github.com/ANRGUSC/JupiterVM.git
    cd JupiterVM/mergetb
    pip3 install -r requirements.txt

### Generate `hosts` file from MergeTB python model 

The python model file (e.g. `mergetb_model.py` in this dir) can be altered for 
your experiment setup on MergeTB. The `host_generator.py` script will extract the
host addresses in the `JUPITER_WORKER_NODES` list and generate a `hosts` file
in the ansible directory. To see an example, generate using the provided mergetb
python model.

    python3 host_generator.py mergetb_model.py

### `cd` into ansible/ and run the following list of commands

Run these **one at a time** and in this order. Check for errors before 
continuing.

    ansible-playbook -K -i hosts common.yml
    ansible-playbook -K -i hosts master.yml
    ansible-playbook -K -i hosts nodes.yml


### Check kubernetes is UP by SSHing into the master node and running

    kubectl get nodes
    kubectl get pods --all-namespaces
