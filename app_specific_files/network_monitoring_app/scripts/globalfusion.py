"""
 * Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pranak Sakulkar, October 2017
 *      Jiatong Wang, October 2017
 *      Aleksandra Knezevic, October 2017
 *      Bhaskar Krishnamachari, October 2017
 *     Read license file in main directory for more details
"""

import os
import time

def write_files(items, outfilename, pathout):
    with open(os.path.join(pathout, outfilename), 'w') as f:
        for item in items:
            f.write(item + '\n')

def task(filelist, pathin, pathout):
    time.sleep(10)
    num = filelist[0].partition('f')[0]

    output_set = set()
    for filename in filelist:
        anomaly_set = set()
        with open(os.path.join(pathin,filename), 'r') as f:
            for line in f.readlines():
                item = line.strip()
                if (item == "*") or ("." not in item):
                    continue
                anomaly_set.add(item)

        print("For file", filename, "anomaly set", anomaly_set)
        output_set = output_set | anomaly_set

    write_files(output_set, num + 'global_anomalies.log', pathout)
    return [os.path.join(pathout, num+'global_anomalies.log')]

def main():

    filelist = ['25fusion_center0.log', '25fusion_center1.log', '25fusion_center2.log']
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile


if __name__ == '__main__':

    filelist = ['25fusion_center0.log', '25fusion_center1.log', '25fusion_center2.log']
    task(filelist, '/home/apac/security_app', '/home/apac/security_app')
