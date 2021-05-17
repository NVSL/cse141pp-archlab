#!/usr/bin/env python3
import re
import sys
from collections import namedtuple
import argparse
import logging as log
import os
import csv
import math
import ast
import unittest

class CalcException(Exception):
    pass
        
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

def ns(d, header=None):
    r = []
    if header is not None:
        r.append(header)
    for k,v in d.items():
        r.append([k,repr(v)])
    return columnize(r, headers=(1 if header != None else 0))

def do_calc(inreader):
    log.info(f"Input fields : {','.join(inreader.fieldnames)}")
    original_fieldnames = inreader.fieldnames
    Field(*inreader.fieldnames[1].split("=", 2))
    fieldnames = [s.split("=", 2)[0] for s in inreader.fieldnames]
    fields = {}
    for s in inreader.fieldnames:
        f = Field(*s.split("=", 2))
        fields[f.name] = f
    
    log.info(f"Output fields: {fields}")

    out=[]
    inreader.fieldnames = fieldnames
    row_num = 0
    for r in inreader:
        row_num += 1
        log.info(f"Parsing {r}")

        # Convert row values into arithmetic values if possible
        for k,v in list(r.items()):
            if fields[k].expression == None and (v is None or v.strip() != ""):
                log.info(f"Parsing '{v}'")
                try:
                    t = ast.literal_eval(v)
                except (ValueError, SyntaxError):
                    t = v
                log.info(f"Parsed '{r[k]}' into {repr(t)}")
                r[k] = t
        log.info(f"parsed literals: {r}")

        for i in range(0, len(fieldnames) + 1): # the longest possible dependence chain is len(fieldnames)
            log.info(f"Pass {i}")
            retry = False
            for k,v in r.items():
                if fields[k].expression != None:
                    cleaned = {k:v for k,v in r.items()}# if v is not None}
                    cleaned.update(dict(math=math))
                    log.info(f"Evaling '{k} = {fields[k].expression}'")
                    log.info(f"Under {ns(cleaned)}")
                    try:
                        r[k] = eval(fields[k].expression, {"__builtins__":None}, cleaned)
                    except Exception as e:
                        if i == len(fieldnames): # it's the last time through the loop, then we really have an error.
                            error_row = [["line"]+ original_fieldnames]+[[row_num] + [r[x] for x in fieldnames]]
                            raise CalcException(f"Expression '{fields[k].expression}' in column '{k}' on row {row_num} is invalid ({e}):\n{columnize(error_row)}") from e
                        retry = True
            if not retry:
                break
            log.info(f"evaluated: {r}")
        out.append(r)

    rows = [fieldnames]
    for o in out:
        rows.append(list(o.values()))
    log.info(f"Result: \n{repr(rows)}")
    log.info(f"Result: \n{columnize(rows)}")
    return rows
    
        
def main():
    parser = argparse.ArgumentParser(description='Perform calculation on CSV files.')
    parser.add_argument('-v', action='store_true', dest="verbose", help="Be verbose")
    parser.add_argument('--out', default="-", dest="output",help="output file")
    parser.add_argument('--in', default="-", dest="input", help="input file")
    cmdline = parser.parse_args()
    log.basicConfig(level=log.DEBUG if cmdline.verbose else log.WARN)
    
    infile = open(cmdline.input) if cmdline.input != "-" else sys.stdin
    inreader = csv.DictReader(infile)

    try:
        output = do_calc(inreader)
    except CalcException as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(1)
        
    outfile = open(cmdline.output, "w") if cmdline.output != "-" else sys.stdout;
    outwriter = csv.writer(outfile)
    for o in output:
        outwriter.writerow(o)
    
if __name__== "__main__":
    main()

class Tests(unittest.TestCase):
    def test_good(self):
        with open("test_inputs/test.csv") as infile:
            inreader = csv.DictReader(infile)
            output = do_calc(inreader)
            
            self.assertEqual(output, [
                ['M', 'e', 'c', 'b', 'a', 'd', 'f'],
                ['f', None, 1, 9, 4, 2.25, 1.5],
                ['f', None, 2, 6, 2, 3.0, 1.7320508075688772]])


    def test_err(self):
        with open("test_inputs/fail.csv") as infile:
            inreader = csv.DictReader(infile)
            with self.assertRaises(CalcException):
                do_calc(inreader)

    def test_div0(self):
        with open("test_inputs/div0.csv") as infile:
            inreader = csv.DictReader(infile)
            with self.assertRaises(CalcException):
                do_calc(inreader)


