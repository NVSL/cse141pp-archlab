
#!/usr/bin/env python

"""This is a simple tool that parses disassembled x86 instructions and
counts the frequence of instructions and addressing modes.  We use it
to determine which x86 instructions we need to teach.

Run it like this:

objdump --disassemble-all <executable> |  ./learnx86.py

"""

import re
import sys

lines = sys.stdin.readlines()

op_hist = dict()
arg_hist = dict()

for l in lines:
    if "file format" in l:
        continue
    if "Disassembly" in l:
        continue
    if "unknown" in l:
        continue
    if re.match("^\s*$", l):
        continue
    if re.search("^\s*\.?[a-zA-Z\_][\w\-\_\.]+:", l):
        continue
    if re.search("\.\.\.", l):
        continue

    g = re.match("\s+([0-9a-f]+):\s+(([0-9a-f][0-9a-f]\s+)+)(\w+)(.*)", l)
    if not g:
        sys.stderr.write("ERR: {}".format(l))
        continue
    
    args=g.group(5).split(", ");
    args = [s.strip() for s in args]
    assert len(args) <= 4, "Too many argument: {} has {}".format(l, len(args))
    op = g.group(4)
    #sys.stdout.write("{addr}|{bytes}|{op}|{args}\n".format(addr=g.group(1), bytes=g.group(2), op=op, args="|".join(args)))
    if op[-1:] in ['b', 's', 'w', 'l', 'q', 't']:
        op = op[0:-1]
    op_hist[op] = op_hist.get(op, 0) + 1


    for a in args:
        types = [
            ("\(\%\w+\)", "(%rax)"),
            ("\%\w+", "%rax"),
            ("\$-?\d+", "$12345"),
            ("-?\d+", "12345"),
            ("-?\d+\(\%\w+\)", "12345(%rax)"),
            ("\(\%\w+,\%\w+\)", "(%rax,%rax)"),
            ("\%\w+:\(\%\w+\)", "%fs:(%rax,%rax)"),
                 ]

        type = None
        for p, n in types:
            if re.match(p, a):
                arg_hist[n] = arg_hist.get(n, 0) + 1
                type = n
        if not type and re.match("", a):
            continue
        assert type, "Unknown addressing mode: {}".format(a)

        

def dump(m):
    hist = []
    total = 0.0
    for k,v in m.items():
        hist.append((v, k))
        total += v 

    sum = 0.0
    for v, k in sorted(hist, reverse=True):
        sum+=v
        sys.stdout.write("{}\t{}\t{:2.3f}%\t{:2.3f}%\n".format(k,v,v/total*100.0,sum/total*100.0))

sys.stdout.write("Instructions\n")
dump(op_hist)

sys.stdout.write("Addressing modes\n")
dump(arg_hist)
