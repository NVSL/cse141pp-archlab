#!/usr/bin/env python3
import sys
import argparse
import logging as log
import os
import csv


def columnize(data, divider="|", headers=1):
    r = ""
    column_count = max(map(len, data))
    rows = [x + ([""] * (column_count - len(x))) for x in data]
    widths = [max(list(map(lambda x:len(str(x)), col))) for col in zip(*rows)]
    div = "{}".format(divider)
    for i, row in enumerate(rows):
        if headers is not None and headers == i:
            r += divider.join(map(lambda x: "-" * (x), widths )) + "\n"
        r += div.join((str(val).ljust(width) for val, width in zip(row, widths))) + "\n"
    return r

def fmt(x):
    try:
        x = float(x)
    except:
        return x
    else:
        return f"{x:.2}"
    
        
        
def main():
    parser = argparse.ArgumentParser(description='Perform calculation on CSV files.')
    parser.add_argument('-v', action='store_true', dest="verbose", help="Be verbose")
    parser.add_argument('--out', default="-", dest="output",help="output file")
    parser.add_argument('--in', default="-", dest="input", help="input file")
    cmdline = parser.parse_args()
    log.basicConfig(level=log.DEBUG if cmdline.verbose else log.WARN)
    
    infile = open(cmdline.input) if cmdline.input != "-" else sys.stdin
    inreader = csv.reader(infile)

    r = []
    for l in inreader:
        r.append(list(map(fmt,l)))
    
    outfile = open(cmdline.output, "w") if cmdline.output != "-" else sys.stdout;
    outfile.write(columnize(r, headers=True, divider='|'))
    
if __name__== "__main__":
    main()
