#!/usr/bin/env python3
import sys
import argparse
import logging as log
import os
import csv

def main():
    parser = argparse.ArgumentParser(description='Perform calculation on CSV files.')
    parser.add_argument('-v', action='store_true', dest="verbose", help="Be verbose")
    parser.add_argument('--field', '-f', nargs=1, default=[0],help="fields to sort by")
    parser.add_argument('--input', '-i',  default="-", nargs=1, help="input file")
    parser.add_argument('--out', default="-", dest="output",help="output file")
    
    cmdline = parser.parse_args()
    log.basicConfig(level=log.DEBUG if cmdline.verbose else log.WARN)
    outfile = open(cmdline.output, "w") if cmdline.output != "-" else sys.stdout;

    column = cmdline.field[0]
    for f in cmdline.input:
        infile = open(f) if f != "-" else sys.stdin
        inreader = csv.DictReader(infile)
        
        r = []
        for l in inreader:
            r.append(l)
            
        writer = csv.DictWriter(outfile,inreader.fieldnames)
        writer.writeheader()
        for row in sorted(r, key=lambda a: a[column]):
            writer.writerow(row)

    

            

if __name__== "__main__":
    main()
