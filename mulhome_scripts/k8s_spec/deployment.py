import yaml

deployment_template = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  labels:
    app: {label}
spec:
  selector:
    matchLabels:
      app: {label}
  template:
    metadata:
      labels:
        app: {label}
    spec:
      nodeSelector:
        kubernetes.io/hostname: {host}
      restartPolicy: Always
      containers:
      - name: jupiter
        imagePullPolicy: Always
        image: {image}
        ports:
        # ports to be filled in using jupiter_config.ini info. example:
        #  - name: ssh
        #   port: 5000
        #   targetPort: 22
        env:
        # env vars to be filled in. examples:
        # - name: CHILD_NODES
        #   value: node2:node3:node5
        # - name: CHILD_NODES_IPS
        #   value: 10.0.0.6:10.0.0.7:10.0.0.9
        # - name: HOME_NODE
        #   value: 10.0.0.2
        # - name: NODE_NAME
        #   value: node1
        # - name: OWN_IP
        # - value: 10.0.0.5
"""

def generate(name, label, image, host, port_mappings, env_vars):
    """Generates a dictionary used for describe k8s services by starting with
    a template.
    """
    depl_spec = deployment_template.format(name=name, label=label, host=host, image=image)
    depl_spec = yaml.load(depl_spec, Loader=yaml.FullLoader)
    depl_spec["spec"]["template"]["spec"]["containers"][0]["ports"] = port_mappings
    env_var_list = []
    for key, value in env_vars.items():
        env_var_list.append({
            "name": key,
            "value": value
        })
    depl_spec["spec"]["template"]["spec"]["containers"][0]["env"] = env_var_list
    return depl_spec