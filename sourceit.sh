sudo chown $(id -u):$(id -g) $HOME/admin.conf
export KUBECONFIG=$HOME/admin.conf #check if it works with `kubectl get nodes` 
source <(kubectl completion bash)
