import paho.mqtt.client as mqtt
import os


def demo_help(server, port, topic, msg):
    username = 'anrgusc'
    password = 'anrgusc'
    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.connect(server, port, 300)
    client.publish(topic, msg, qos=1)
    client.disconnect()


def convert_bytes(num):
    """Convert bytes to Kbit as required by HEFT

    Args:
        num (int): The number of bytes

    Returns:
        float: file size in Kbits
    """
    return num * 0.008


def file_size(file_path):
    """Return the file size in bytes

    Args:
        file_path (str): The file path

    Returns:
        float: file size in bytes
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)
