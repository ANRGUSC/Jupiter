import sys
from collections import deque
import json
import logging


logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


# rotate task mapping by 1
def rotate(infile, outfile):
    with open(infile, "r") as f:
        input_mapping = json.load(f)

    values = deque(input_mapping.values())
    values.rotate(1)

    output_mapping = dict(zip(input_mapping.keys(), values))

    with open(outfile, "w") as f:
        json.dump(output_mapping, f, indent=4)


if __name__ == '__main__':
    if len(sys.argv) == 4:
        if sys.argv[1] == "rotate":
            rotate(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == "random":
            log.error("option random to be implemented")
            exit()

        log.info(f"Created output file {sys.argv[3]}")
    else:
        log.error("OPTION: rotate or random")
        log.error("usage: python alter_mapping.py {OPTION} {infile} {outfile}")
        exit()
