#!/usr/bin/env python
# encoding: utf-8
#JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini' #docker
JUPITER_CONFIG_INI_PATH = '../../jupiter_config.ini' # local

EXP_ID = 'c'

CODING_PART1 = 0
RESNETS_THRESHOLD = 3 #1 or 3

CODING_PART2 = 1

EXP_NAME = 'sleep'
STRAGGLER_THRESHOLD = 0
SLEEP_TIME = 5 #0 or 5

MASTER_POLL_INTERVAL = 2 
RESNET_POLL_INTERVAL = 1
MASTER_TO_RESNET_TIME = 10

STREAM_INTERVAL = 60
NUM_IMAGES = 100
NUM_CLASS =11
NUM_DATASOURCES = 100
classlist = ['fireengine', 'schoolbus', 'whitewolf',  'tiger', 'kitfox', 'persiancat', 'leopard',   'americanblackbear', 'mongoose', 'zebra',  'hippopotamus',  'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter','ox','lion','hog','hyena']
