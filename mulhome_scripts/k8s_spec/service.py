import yaml

service_template = """
apiVersion: v1
kind: Service
metadata:
  name: {name}
  labels:
    purpose: jupiter
spec:
  ports:
  # to be filled using jupiter_config.ini info
  selector:
    app: {name}
"""

def generate(name, port_mappings):
    """Generates a dictionary used for describe k8s services by starting with
    a template.
    """
    service_spec = service_template.format(name=name)
    service_spec = yaml.load(service_spec, Loader=yaml.FullLoader)
    service_spec["spec"]["ports"] = port_mappings
    return service_spec