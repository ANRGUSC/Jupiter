#!/usr/bin/env python
# encoding: utf-8
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini' #docker
#JUPITER_CONFIG_INI_PATH = '../../jupiter_config.ini' # local
CODING_PART1 = 1
RESNETS_THRESHOLD = 3 #1 or 3

CODING_PART2 = 1

EXP_NAME = 'sleep'
EXP_ID = 'ne'

SLEEP_TIME = 5 #0 or 5
MASTER_POLL_INTERVAL = 2 
RESNET_POLL_INTERVAL = 1
MASTER_TO_RESNET_TIME = 10
STRAGGLER_THRESHOLD = 0
STREAM_INTERVAL = 120

NUM_IMAGES = 50
NUM_CLASS =11
classlist = ['fireengine', 'schoolbus', 'whitewolf',  'tiger', 'kitfox', 'persiancat', 'leopard',  'mongoose', 'americanblackbear','zebra',  'hippopotamus',  'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter','ox','lion','hog','hyena']
