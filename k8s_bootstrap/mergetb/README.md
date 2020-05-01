Ansible playbooks were modeled after those found in:
https://github.com/kairen/kubeadm-ansible.

### Known Issues

 * These directions only support **Ubuntu and Debian**.
 * DCOMP Ubuntu 18.04 images do not have `/usr/bin/python` but does have 
   `/usr/bin/python3` so we have defaulted ansible to using `python3`
 * coredns pods will be scheduled on the master node due to the order of 
   commands in the ansible playbooks, which is the preferred  behavior. If the 
   pods are restarted, they may be scheduled on k8s worker nodes.
 * `iptables` v1.8+ may cause problems and switching it to legacy mode is
   included in the playbooks. More information in troubleshooting section below.

### Learning MergeTB

Using MergeTB requires learning the GUI and vocabulary. These instructions were
built from our experience through https://www.mergetb.org/gui/walkthrough/. If
something is unclear here, please cross-reference the walkthrough.

### Setup MergeTB and Workspace

##### Create an Experiment on MergeTB (aka DCOMP Testbed)

First, prepare your cloud nodes via an "experiment" in MergeTB. An "experiment"
can be seen as a collection of cluster instances where each instance is a
"realization." Login to https://launch.mergetb.net, create a project, and create 
an experiment. To run the scripts in this repository, you can use the provided
model mergetb_model.py. In the Models tab of the UI, upload mergetb_model.py. 
Then, click on the new model and click on "Push to Experiment". Select the 
experiment that you created. If you used the example model, three nodes in total
 will be created with the hostnames `master`, `n0`, `n1`, etc. 

 * Do **not** realize or materialize an experiment yet because SSH keys need to 
   be generated first
 * Create an xdc ("eXperiment Development Container") and navigate to the Jupyter
   notebook link
 * In Jupyter under the "Files" tab, click on the drop down menu labeled "New" 
   and click on "Terminal"
 * `su {YOUR_MERGETB_USERNAME}` 
   * ignore authentication failure message

##### Generate Key for the xdc

To easily SSH into all nodes in a "realization," you will need to setup keys 
using your xdc. If you decide to create new xdc's, you will need to repeat this
process.

In the xdc terminal, create an ssh key by executing `ssh-keygen`. The default
public key can be found in `~/.ssh/id_rsa.pub`. On launch.mergetb.net, go to
the "User Profiles" page. On the right side, add a key and upload the public
key file (i.e., id_rsa.pub). This will let you SSH from the xdc to any 
experiment nodes *that are realized after 

##### SSHing to the xdc from Your Local Machine

Replace text with curly braces with project specific values.

 * Add your machine's pub key to the xdc via a Jupyter terminal
   * Append to ~/.ssh/authorized_keys in *your* home directory in the xdc
 * Take note of your xdc's reference name to the right of the Jupyter link

On your Ubuntu 16.04 (openssh ver. 7.2 and lower) local machine:

 * Test your connection:
    * `ssh -o ProxyCommand="ssh -W %h:%p jumpc.mergetb.io -p 2202" {USERNAME}@{XDC_REFERENCE_NAME}`
    * xdc's seem to break the pipe without keepalive packets so more setup is needed
 * Append the following to your local machine's ~/.ssh/config (note the 
   ServerAliveInterval is necessary to prevent broken pipes!):

```
    Host *-{PROJECT_NAME}
      Hostname %h
      User {USERNAME}
      ProxyCommand ssh jumpc.mergetb.io -p 2202 -W %h:%p
    Host *
      ServerAliveInterval 100
      ServerAliveCountMax 2
```

 * Then, simply `ssh xdc-{EXPERIMENT}-{PROJECT}`

On your Ubuntu 18.04 (openssh ver. 7.3+) local machine: 

 * `ssh -J jumpc.mergetb.io:2202 {USERNAME}@{XDC_REFERENCE_NAME}`
 * Alternatively, you can append the following to your local machine's 
 ~/.ssh/config (note the ServerAliveInterval is necessary to prevent broken pipes!):

```
    Host *-{PROJECT_NAME}
      Hostname %h
      User {USERNAME}
      ProxyJump {USERNAME}@jumpc.mergetb.io:2202
    Host *
      ServerAliveInterval 100
      ServerAliveCountMax 2
```

 * Then, simply `ssh xdc-{EXPERIMENT}-{PROJECT}`

##### Materialize a Realization and Attach xdc

 * Navigate to the experiment page, click on "+" next to the model under the 
"Versions" section to realize the mergetb model.
 * Navigate to the new realization and click "Accept" followed by "Materialize"
 * In your xdc: 
    * `mergetb login {USERNAME}`
    * `attach {PROJECT_NAME} {EXPERIMENT_NAME} {REALIZATION_NAME}`

Try to SSH into a node, e.g. `ssh {HOSTNAME}`. If you are having problems, 
`detach` and then `attach` again.

### Bootstrap Kubernetes in Realization

In your xdc, execute

    sudo apt update
    sudo apt upgrade -y

Then,

    sudo apt install git -y
    git clone https://github.com/ANRGUSC/Jupiter.git
    cd Jupiter/mergetb
    pip3 install -r requirements.txt

##### Generate `hosts` file from MergeTB python model 

The python model file, such as the example in `mergetb_model.py`, can be altered for 
your experiment setup on MergeTB. The `host_generator.py` script will extract the
host addresses in the `JUPITER_*_NODES` list and generate a `hosts` file
in this directory. To generate one for the example,

    python3 host_generator.py mergetb_model.py

##### Use Ansible to Bootstrap

The Ansible playbooks have been designed for idempotency. To better understand
our setup method or debug it, please look deeper into the playboooks. Bootstrap
the cluster by running

    ansible-playbook -i hosts site.yml 

The playbooks should move `admin.conf` from the master node to your xdc with
destination `${HOME}/.kube/config` to allow you to use `kubectl` from the xdc.

To reset the k8s cluster, run

    ansible-playbook -i hosts reset-site.yml

Some notes:

 * You can run with the flag `-v` (add more `v`s to increase verbosity) to see
 the results of each playbook task
 * You can run the playbooks multiple times
 * The playbooks only support Ubuntu and Debian and detect which OS is being 
 used per node so, in theory, you can have a heterogeneous cluster of Ubuntu/
 Debian

##### Check k8s Status

Install `kubectl` using the official doc pages. Check if your cluster is up.

    kubectl get nodes
    kubectl get pods --all-namespaces

To use `kubectl` in the master node, log into `root` user, `sudo -i`.

##### Test k8s Networking

To test if k8s networking is working, launch an nginx container and curl the
webserver contents from a busyboxplus container.

```
    kubectl run --image=nginx nginx-app --port=80
    kubectl expose pod nginx-app --port=80 --name=nginx-http
    kubectl get svc #take note of nginx-http service IP
    kubectl run curl --image=radial/busyboxplus:curl -i --tty -- /bin/sh
    curl nginx-http #test DNS
    curl {NGINX_HTTP_SERVICE_IP}
```

### Troubleshooting

##### `iptables` breaks your cluster

Debian recently upgraded `iptables` to v1.8, which is a key component for
routing in Kubernetes. In v1.8, the commands look and feel the same, but because
the user-space `iptables` tool is tightly integrated with the kernel subsystem,
a Docker container running commands via iptables&lt;v1.8 on a host which has
iptables>=v1.8 will not work properly. Because Ubuntu, Kubernetes, and much of
the container world has not yet moved to v1.8, this will cause problems in the
future or for any nodes running Debian Buster or greater. As a first-level patch
for this, each k8s node can run:

    sudo update-alternatives --set iptables /usr/sbin/iptables-legacy

The common.yml playbook already detects the iptables version and sets legacy 
mode where applicable. K8s/Jupiter users should be aware of this through time in
the event an update is pushed downstream to lower iptables versions. More
information can be found here: 
https://github.com/kubernetes/kubernetes/issues/71305

##### coredns problems

If DNS is failing, you can try to erstart the coredns pods update tables.

    kubectl -n kube-system delete pods -l k8s-app=kube-dns

Please note the k8s scheduler will likely move the coredns pods to a worker 
node. If you used the ansible scripts to boostrap the k8s cluster, the coredns
pods will run on the master node, which is the preferred behavior for using
Jupiter. Jupiter wants to leave all `kube-system` pods on the master node since
Jupiter does not rely on the Kubernetes scheduler (it wants to manage the
resources of each worker node).

### Upgrading Kubernetes

If there is a need to upgrade Kubernetes, try these changes. We have not yet
attempted any upgrades.

The ansible plays will create a hold on kubernetes packages. Temporarily create
a task which will unhold the packages, install the updates, and then hold them
again. You can also create a new cluster from scratch.
