"""
    This script generates all possible combination of links in a fully connected network of the droplet for further network profiling procedure.
"""
__author__ = "Quynh Nguyen, Pradipta Ghosh, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import pandas as pd
import itertools

def main():
    """
        Read ``central_input/nodes.txt`` to get the list of nodes and output combination of link lists in ``central_input/link_list.txt``.
    """
    print('Preparing the link list text files')
    input_node_info_file   = 'central_input/nodes.txt'
    output_link_list       = 'central_input/link_list.txt'

    """
        read the input csv fine to get the list of nodes
    """
    input_node_info = pd.read_csv(input_node_info_file, header = 0, delimiter = ',', index_col = 0)
    input_node_list = input_node_info.T.to_dict('list')

    with open(output_link_list, 'w') as f:
        # first line of the output csv file
        f.write('Source,Destination\n')

        for node_pair in itertools.combinations(input_node_list.keys(),2):
            # output the generated node pair separeated by a comma (,)
            f.write(",".join(node_pair)+"\n")
        
            # output the reverse node pair separeated by a comma (,).
            # The "::-1" index reverses the node pair.
            f.write(",".join(node_pair[::-1])+"\n")

if __name__ == '__main__':
    main()