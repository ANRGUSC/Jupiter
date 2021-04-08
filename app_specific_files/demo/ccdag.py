#!/usr/bin/env python
# encoding: utf-8
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini' #docker
#JUPITER_CONFIG_INI_PATH = '../../jupiter_config.ini' # local

"""
Classification Coding

Set to 1 to enable or 0 to disable. When classifciation coding is on (or
"Part 1 Coding"), the master service task will detect if one of the resnet
tasks are straggling (currently done by injecting delays at resnet8 via a sleep
to emulate straggling). If there is a straggler, the master servicewill
manually forward an image to a storeclass task to compensate for the straggler.

Every image the master service task receives from a datasource will be
forwarded to all resnet tasks. It will then block until enough resnet tasks are
finished classifying that same image. All resnet tasks will POST to a flask
container called "Glboal Info" maintaining a key value store (kvstore) of the
resnet tasks that are finished with an image.

Each image is considered a "job" with a corresponding ID number. The
RESNETS_THRESHOLD setting indicates how many resnet stragglers CCDAG can
tolerate. That is, if RESNETS_THRESHOLD=1, then the master service will send
the next image job to all the resnet tasks. Currently, the implementation only
supports injecting delays (to emulate "straggling") at resnet8. This means we
currently do not support RESNETS_THRESHOLD values greater than 1. If part 1
coding is disabled, *you must set the threshold to 0*.

The master service keeps tabs on the finished resnets tasks by polling the
kvstore container every MASTER_POLL_INTERVAL seconds to check on the status of
resnet job completion. We have kept this value at 1 second, so it is best to
keep it at this value.

The master service will poll the kvstore container up to RESNET_DEADLINE
seconds. After that time, the master service will consider there to be too many
resnet stragglers, so it will manually forward the image that was sent to the
resnets directly to the corresponding storeclass task (e.g. a fire engine image
will be sent to storeclass1). This emulates the job of the
"collage worker task" which is supposed to do this, but is currently not
implemented.

The RESNET_POLL_INTERVAL is the interval in seconds in which a resnet task will
poll the kvstore flask container to see if an image job is complete. This is
because resnet tasks are supposed to block until enough of the resnet tasks are
finished trying to classify the image. If the master service ends up forwarding
the image directly, I believe the master service will update the kvstore flask
container accordingly to notify the blocking resnet tasks.
"""
CODING_PART1 = 1            # 1 to enable, 0 to disable
RESNETS_THRESHOLD = 1
MASTER_POLL_INTERVAL = 2    # Seconds
RESNET_DEADLINE = 10        # Seconds
RESNET_POLL_INTERVAL = 1    # Seconds


"""
Correlation Coding:

Set CODING_PART2 to 1 to enable or 0 to disable. Correlation Coding (or
"Part2 Coding") will tolerate up to one score task to straggle such that CCDAG
can still successfully correlate the input image job to the set of all
reference images of that branch's class (see the `reference` folder). That is,
only 2 of 3 score tasks in each branch need to complete the scoring (i.e.
correlation) task for a job to finish.

When coding is enabled, the preagg task will move forward with just two scores
and not bother waiting for the third. When coding is disabled, the preagg task
will wait for the straggler to finish before moving forward.
"""
CODING_PART2 = 1

"""
Injecting Delays at resnet8 and score#a for "Straggling"

For each image to classify, resnet8 will generate a random float (0, 1]. If the
value is greater than STRAGGLER_THRESHOLD, resnet8 will sleep for SLEEP_TIME
seconds. SLEEP_TIME=0 disables any injected delays.

All score#a tasks will also inject a delay using the same method and parameters
as resnet8.
"""
SLEEP_TIME = 5          #Seconds
STRAGGLER_THRESHOLD = 0

# This is used for naming the results and plots in generate_results.py
EXP_NAME = 'sleep'
EXP_ID = 'a'

# All datasource tasks will send images to the master service with the designated
# interval below
STREAM_INTERVAL = 120   # Seconds

# Total images each datasource will stream into CCDAG. (e.g. if there are two
# datasources and NUM_IMAGES=50, there will be 100 total images)
NUM_IMAGES = 50

# Number of image classes (in the sequence of the `classlist` below)
# datasources will send to the master service. e.g. setting it to "2" will tell
# datasources to stream only 'fireengine' and 'schoolbus' images.
NUM_CLASS = 2
classlist = ['fireengine', 'schoolbus', 'whitewolf',  'tiger', 'kitfox', 'persiancat', 'leopard',  'mongoose', 'americanblackbear','zebra',  'hippopotamus',  'waterbuffalo', 'ram', 'impala', 'arabiancamel', 'otter','ox','lion','hog','hyena']
