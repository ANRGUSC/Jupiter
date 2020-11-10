#!/usr/bin/env python
# encoding: utf-8
#JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini' #docker
JUPITER_CONFIG_INI_PATH = '../../jupiter_config.ini' # local
CODING_PART1 = 1
CODING_PART2 = 1
EXP_NAME = 'nosleep'
EXP_ID = 'b'
SLEEP_TIME = 5 #0 or 5
MASTER_POLL_INTERVAL = 2 
RESNET_POLL_INTERVAL = 1
MASTER_TO_RESNET_TIME = 10
STRAGGLER_THRESHOLD = 0
RESNETS_THRESHOLD = 1 #1 or 3
STREAM_INTERVAL = 10
NUM_IMAGES = 100
NUM_CLASS =11
# classlist = ['fireengine', 'schoolbus', 'whitewolf', 'hyena', 'tiger', 'kitfox', 'persiancat', 'leopard', 'lion',  'americanblackbear', 'mongoose', 'zebra', 'hog', 'hippopotamus', 'ox', 'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter']
classlist = ['fireengine', 'schoolbus', 'whitewolf',  'tiger', 'kitfox', 'persiancat', 'leopard',   'americanblackbear', 'mongoose', 'zebra',  'hippopotamus',  'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter','hyena','ox','lion','hog']
