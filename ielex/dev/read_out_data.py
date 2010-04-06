#!/usr/bin/env python
"""
Usage: get_data.py [START_INDEX [END_INDEX]]
"""
import sys
import subprocess
START = 142

def main():
    fileobj = file("ielex-wiki-swadesh-ids.csv")
    fileobj.next()
    data = []
    for line in fileobj:
        row = line.strip().split("\t")
        if row[1]:
            data.append((int(row[1]), row[2]))
    for row in sorted(data):
        if row[0] >= START:
            for elem in row:
                subprocess.call(["say", '"%s"' % elem])
    return

if __name__ == "__main__":
    main()
