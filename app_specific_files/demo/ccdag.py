#!/usr/bin/env python
# encoding: utf-8
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini' #docker
#JUPITER_CONFIG_INI_PATH = '../../jupiter_config.ini' # local
CODING_PART1 = 0
RESNETS_THRESHOLD = 1 #1 (non-coding) or 3 (coding)

CODING_PART2 = 1

EXP_NAME = 'sleep'
EXP_ID = 'test'

SLEEP_TIME = 30
MASTER_POLL_INTERVAL = 7 
RESNET_POLL_INTERVAL = 2
MASTER_TO_RESNET_TIME = 38
STRAGGLER_THRESHOLD = 0
STREAM_INTERVAL = 10

NUM_IMAGES = 100
NUM_CLASS =2
classlist = ['fireengine', 'schoolbus', 'whitewolf',  'tiger', 'kitfox', 'persiancat', 'leopard',   'americanblackbear', 'mongoose', 'zebra',  'hippopotamus',  'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter','ox','lion','hog','hyena']
