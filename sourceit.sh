# add this to your .bashrc to avoid using this
source <(kubectl completion bash)

# TODO: add .bashrc instructions to README instead of using this script
sudo chown $(id -u):$(id -g) $HOME/admin.conf
export KUBECONFIG=$HOME/admin.conf #check if it works with `kubectl get nodes`
source <(kubectl completion bash)
