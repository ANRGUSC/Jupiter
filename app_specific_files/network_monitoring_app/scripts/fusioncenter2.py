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

def write_files(filename, fusion_center, pathout):
    with open(os.path.join(pathout, fusion_center), 'w') as f:
        for item in filename:
            f.write(item + '\n')

def task(filelist, pathin, pathout):
    time.sleep(10)
    num = filelist[0].partition('a')[0]

    output_set = set()
    for filename in filelist:
        anomaly_set = set()
        with open(os.path.join(pathin,filename), 'r') as f:
            for line in f.readlines():
                s_list = line.strip().replace(" ", ":").replace(";", ":").split(":")
                for item in s_list[:4]:
                    if (item == "*") or ("." not in item):
                        continue
                    anomaly_set.add(item)

        print("For file", filename, "anomaly set", anomaly_set)
        output_set = output_set | anomaly_set


    write_files(output_set, num+'fusion_center2.log', pathout)
    return [os.path.join(pathout, num+'fusion_center2.log')]

def main():

    filelist = ['25anomalies_simple2.log', '25anomalies_astute2.log', '25anomalies_dft2.log', '25anomalies_tera2.log']
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':

    filelist = ['25anomalies_simple2.log', '25anomalies_astute2.log']
    task(filelist, '/home/apac/security_app', '/home/apac/security_app')
