from os import path
import os
import configparser

HERE                    = path.abspath(path.dirname(__file__)) + "/"
INI_PATH                = HERE + 'jupiter_config.ini'

config = configparser.ConfigParser()
config.read(INI_PATH)

STATIC_MAPPING          = int(config['CONFIG']['STATIC_MAPPING'])
DISTRIBUTED             = int(config['CONFIG']['DISTRIBUTED'])
STATIC_EXEC             = int(config['CONFIG']['STATIC_EXEC'])

USERNAME                = config['AUTH']['USERNAME']
PASSWORD                = config['AUTH']['PASSWORD']

RP_PORT                 = config['PORT']['RESOURCE']
NW_PORT                 = config['PORT']['NETWORK']
EXC_MPORT               = config['PORT']['MONGO_SVC']
EXC_FPORT               = config['PORT']['FLASK_SVC']
SSH_PORT                = config['PORT']['SSH_SVC']
WAVE_PORT               = config['PORT']['WAVE_EXPOSE']
HEFT_PORT               = config['PORT']['HEFT_EXPOSE']
CIRCE_PORT              = config['PORT']['FLASK_DOCKER']

MAX_LOG                 = int(config['OTHER']['MAX_LOG'])
