#!/usr/bin/env python3
import re
import sys
from collections import namedtuple
import argparse
import logging as log
import os
import csv
import math

class Field(object):
    def __init__(self, name, expression=None):
        self.name = name
        self.expression = expression
    def __str__(self):
        return f"({self.name}, {self.expression})"
    def __repr__(self):
        return f"({self.name}, {self.expression})"

def columnize(data, divider="|", headers=1):
    r = ""
    column_count = max(map(len, data))
    rows = [x + ([""] * (column_count - len(x))) for x in data]
    widths = [max(list(map(lambda x:len(str(x)), col))) for col in zip(*rows)]
    div = " {} ".format(divider)
    for i, row in enumerate(rows):
        if headers is not None and headers == i:
            r += "-" * (sum(widths) + len(rows[0]) * len(div))  + "\n"
        r += div.join((str(val).ljust(width) for val, width in zip(row, widths))) + "\n"
    return r

        
def main():
    parser = argparse.ArgumentParser(description='Perform calculation on CSV files')
    parser.add_argument('-v', action='store_true', dest="verbose", help="Be verbose")
    parser.add_argument('--out', default="-", dest="output",help="output file")
    parser.add_argument('--in', default="-", dest="input", help="input file")
    cmdline = parser.parse_args()
    log.basicConfig(level=log.DEBUG if cmdline.verbose else log.WARN)
    
    infile = open(cmdline.input) if cmdline.input != "-" else sys.stdin

    inreader = csv.DictReader(infile)

    log.info(f"Input fields : {','.join(inreader.fieldnames)}")
    Field(*inreader.fieldnames[1].split("=", 2))
    fieldnames = [s.split("=", 2)[0] for s in inreader.fieldnames]
    fields = {}
    for s in inreader.fieldnames:
        f = Field(*s.split("=", 2))
        fields[f.name] = f
    
    log.info(f"Output fields: {fields}")

    out=[]
    inreader.fieldnames = fieldnames
    for r in inreader:
        log.info(f"Parsing {r}")
        for k,v in list(r.items()):
            if fields[k].expression == None:
                t = eval(r[k],{}, {})
                log.info(f"Parsed '{r[k]}' into {repr(t)}")
                r[k] = t
        log.info(f"parsed literals: {r}")

        for i in range(0, len(fieldnames) + 1): # the longest possible dependence chain is len(fieldnames)
            retry = False
            for k,v in r.items():
                if fields[k].expression != None:
                    cleaned = {k:v for k,v in r.items() if v is not None}
                    cleaned.update(dict(math=math))
                    try:
                        r[k] = eval(fields[k].expression, {"__builtins__":None}, cleaned)
                    except Exception as e:
                        if i == len(fieldnames): # it's the last time through the loop, then we really have an error.
                            raise Exception(f"Expression '{fields[k].expression}' in column '{k}' is invalid: {e}") from e
                        retry = True
            if not retry:
                break
            log.info(f"evaluated: {r}")
        out.append(r)
        
    outfile = open(cmdline.output) if cmdline.output != "-" else sys.stdout;
    outwriter = csv.DictWriter(outfile, fieldnames=fieldnames)
    outwriter.writeheader()
    rows = [fieldnames]
    for o in out:
        outwriter.writerow(o)
        rows.append(list(o.values()))
    
    log.info(f"Result: \n{columnize(rows)}")

if __name__== "__main__":
    main()
