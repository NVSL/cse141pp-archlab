#!/usr/bin/env python3
import sys
import argparse
import logging as log
import os
import csv
from .csvpretty import prettify_dicts

def main():
    parser = argparse.ArgumentParser(description='Merge csv files.')
    parser.add_argument('-v', action='store_true', dest="verbose", help="Be verbose")
    parser.add_argument('--out', default="-", dest="output",help="output file")
    parser.add_argument('--add-file', default=False, action='store_true', help="add the file name to each row")
    parser.add_argument('input', default="-", nargs="+", help="input files")
    parser.add_argument('--pretty', '-p', action="store_true", default=False, help="pretty print the result")
    
    cmdline = parser.parse_args()
    log.basicConfig(level=log.DEBUG if cmdline.verbose else log.WARN)
    outfile = open(cmdline.output, "w") if cmdline.output != "-" else sys.stdout;

    
    keys = []
    all_rows = []
    for f in cmdline.input:
        with open(f) as infile:
            reader = csv.DictReader(infile)
            if cmdline.add_file:
                names = ['_file'] + reader.fieldnames
            else:
                names = reader.fieldnames
            for k in names:
                if k not in keys:
                    keys.append(k)
#            keys.update(reader.fieldnames)
            for row in reader:
                if cmdline.add_file:
                    row['_file'] = f
                all_rows.append(row)
    if cmdline.pretty:
        outfile.write(prettify_dicts(all_rows))
    else:
        writer = csv.DictWriter(outfile,keys)
        writer.writeheader()
        for r in all_rows:
            writer.writerow(r)

    
if __name__== "__main__":
    main()
