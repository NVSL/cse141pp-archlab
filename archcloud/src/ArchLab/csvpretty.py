#!/usr/bin/env python3
import sys
import argparse
import logging as log
import os
import csv


def columnize(data, divider="|", header=1):
    r = ""
    column_count = max(map(len, data))
    rows = [x + ([""] * (column_count - len(x))) for x in data]
    widths = [max(list(map(lambda x:len(str(x)), col))) for col in zip(*rows)]
    div = "{}".format(divider)
    for i, row in enumerate(rows):
        if header is not None and header == i:
            r += divider.join(map(lambda x: "-" * (x), widths )) + "\n"
        r += div.join((str(val).ljust(width) for val, width in zip(row, widths))) + "\n"
    return r

def fmt(x):
    try:
        x = float(x)
    except:
        return x
    else:
        return f"{x:.3}"
    
def prettify_dicts(rows):
    heads = list(rows[0].keys())
    out = [heads]
    for r in rows:
        out += [[fmt(r[a]) for a in heads]]

    return columnize(out, header=True, divider='|')

def prettify_rows(rows, header=False):
    out = []
    for r in rows:
        out += [[fmt(a) for a in r]]
    return columnize(out, header=header, divider='|')
    
def main():
    parser = argparse.ArgumentParser(description='Perform calculation on CSV files.')
    parser.add_argument('-v', action='store_true', dest="verbose", help="Be verbose")
    parser.add_argument('--out', default="-", dest="output",help="output file")
    parser.add_argument('input', default="-", nargs="+", help="input files")
                    
    cmdline = parser.parse_args()
    log.basicConfig(level=log.DEBUG if cmdline.verbose else log.WARN)
    outfile = open(cmdline.output, "w") if cmdline.output != "-" else sys.stdout;

    for f in cmdline.input:
        infile = open(f) if f != "-" else sys.stdin
        inreader = csv.reader(infile)
        
        r = []
        for l in inreader:
            r.append(list(l))
        outfile.write(prettify_rows(r, header=True))
    
if __name__== "__main__":
    main()
