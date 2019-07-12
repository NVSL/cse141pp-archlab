#!/usr/bin/env python

"""
Tool for renaming x86 instruction traces and plotting dependences between instructions. 

Run it like this to print out a table showing the instructions with renamed registers and the renaming table:

./rename-x86.py < test.s 

Run it like this to format the dependecies with graphviz:

./rename-x86.py --dot  < test.s |dot -Tpdf > t.pdf; open t.pdf

It only handles a subset of x86.

"""

import re
import sys
from collections import namedtuple
import argparse
import logging as log

parser = argparse.ArgumentParser(description='Rename an x86 instruction trace')
parser.add_argument('--dot', nargs=1, help="Output the DFG in dot")
parser.add_argument('--csv', nargs=1, help="Output the timeline as csv")
parser.add_argument('-v', action='store_true', dest="verbose", help="Be verbose")
parser.add_argument('--no-rename', action='store_false', dest="rename", default=True, help="Be verbose")
cmdline = parser.parse_args()

if cmdline.dot:
    dot_file = open(cmdline.dot[0], "w")
if cmdline.csv:
    csv_file = open(cmdline.csv[0], "w")

log.basicConfig(level=log.DEBUG if cmdline.verbose else log.WARN)

def columnize(data, divider="", headers=None):
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


lines = sys.stdin.readlines()

op_hist = dict()
arg_hist = dict()

x86_registers = [
    "ax",
    "bx",
    "cx",
    "dx",
    "sp",
    "si",
    "bp",
    "r8",
    "r9",
    "r10",
    "r11",
    "r12",
    "r13",
    "r14",
    "r15",
    "si",
    "di",
    "ip",
    "flags"
]

x86_any_reg = "\%((|e|r)({}))d?".format("|".join(x86_registers))

AddrMode = namedtuple("AddrMode", "re ex count")

x86_addressing_modes = [
    AddrMode("\({reg}\)", "(%rax)", 1),
    AddrMode("{reg}", "%rax", 1),
    AddrMode("\$-?\d+", "$12345", 0),
    AddrMode("-?\d+", "12345", 0),
    AddrMode("-?\d+\({reg}\)", "12345(%rax)", 1),
    AddrMode("\({reg},{reg}\)", "(%rax,%rax)", 2),
    AddrMode("{reg}:\({reg},{reg}\)", "%fs:(%rax,%rax)", 3),
    ]

def regify(x):
    return "^{}$".format(x.format(reg=x86_any_reg))

class Inst(object):
    def __init__(self, name, ins, outs, ignore=None):
        self.name = name
        self.ins = ins
        self.outs = outs
        if ignore is None:
            ignore = []
        self.arg_count = len(set(filter(lambda x: isinstance(x, int), ins + outs + ignore)))
        log.debug("defined inst: {} {} {} {}".format(name, ins, outs, self.arg_count))

def arith(x, op, set_flags=False): 
    return Inst(x, ins=[0, 1], outs=[1] + (["flags"] if set_flags else []))

x86_instructions = [
    arith("add", "+"),
    arith("xor", "^"),
    arith("imul", "*"),
    arith("sub", "-", set_flags=True),
    arith("and", "&"),
    arith("shl", "<<"),
    arith("sal", "<<"),
    arith("shr", ">>"),
    arith("sar", "<<"),
    Inst("sar", ins=[0], outs=[0]),
    Inst("neg", ins=[0], outs=[0]),
    Inst("imul", ins=[0], outs=["dx", "ax"]),
    Inst("j", ins=[0], outs=[]),
    Inst("cmp", ins=[0,1], outs=["flags"]),
    Inst("inc", ins=[0], outs=[0]),
    Inst("test", ins=[0,1], outs=["flags"]),
    Inst("lea", ins=[0], outs=[1]),
    Inst("mov", ins=[0], outs=[1]),
    Inst("jne", ins=[0, "flags"], outs=[]),
    Inst("jle", ins=[0, "flags"], outs=[]),
    Inst("je", ins=[0, "flags"], outs=[]),
    Inst("jae", ins=[0, "flags"], outs=[]),
    Inst("jg", ins=[0, "flags"], outs=[]),
    Inst("jge", ins=[0, "flags"], outs=[]),
    Inst("cmovne", ins=["flags", 0], outs=[1]),
    Inst("jmp", ins=[0], outs=[]),
    Inst("pop", ins=["sp"], outs=[0, "sp"]),
    Inst("push", ins=[0, "sp"], outs=["sp"]),
    Inst("ret", ins=["ax"], outs=[]),
    Inst("ret", ins=[0], outs=[]),
]
    
x86_inst_map = {(x.name, x.arg_count): x for x in x86_instructions}

def get_regs(mode, match):
    r = []
    return r

rat = {x[1]: x[0] for x in enumerate(x86_registers)}
next_free_reg = len(x86_registers)

last_writer = {x:None for x in x86_registers + range(0, len(x86_registers))}
last_reader = {x:None for x in x86_registers + range(0, len(x86_registers))}
dependence_depth = {x:0 for x in map(lambda y:"pr{}".format(y), range(0, len(x86_registers))) + x86_registers}
inst_depths = {}

if cmdline.dot:
    dot_file.write("digraph trace {")

output = []
output.append(["line num", "code", "depth", "ins", "outs", "renamed_ins", "renamed_outs"] + x86_registers)


inst_id = 0 
inst_count = 0 
max_depth = 0
for l in lines:
    log.debug("Analyzing {}".format(l))
    inst_id += 1
    l = re.sub("\#.*", "", l);


    discard_patterns = [
        "file format",
        "Disassembly",
        "unknown",
        "^\s*\.\w+.*",
        "^\s*\w+:.*",
        "\.",
        "\.\.\."]
    skip = False

    for p in discard_patterns:
        if re.search(p, l):
            skip = True
            log.debug("Skipping '{}' because it matches '{}'".format(l, p))
            break
    if skip:
        continue

    if re.match("^\s*$", l):
        log.debug("Skipping empty line: '{}'".format(l))
        continue;
    
    # match a line of x86 assembly.
    g = re.match("\s*(\w+)(.*)", l)
    if not g:
        log.error("Malformed line: {}".format(l))
        sys.exit(1)
        continue
    inst_count += 1

    args=g.group(2).split(", ");
    args = [s.strip() for s in args]
    
    assert len(args) <= 4, "Too many argument: {} has {}".format(l, len(args))
    op = g.group(1)
    if op[-1:] in ['b', 's', 'w', 'l', 'd', 'q']:
        op = op[0:-1]

    inst = x86_inst_map.get((op, len(args)))

    if not inst:
        log.error("Unknown instruction: {} ({} args)".format(op, len(args)))
        sys.exit(1)
        continue;
    inputs = []
    outputs = []

    
    def get_reg_ios(ios):
        r = []
        for i in ios:
            if isinstance(i, str):
                r.append(i)
                continue
        
            a = args[i]
            found = True
            for am in x86_addressing_modes:
                m = re.match(regify(am.re), a)
                if m:
                    log.debug("Argument '{}' matched addressing mode {}".format(a, am.re))
                    for k in range(0, am.count):
                        whole_reg_name = m.group(3*k + 1)
                        gp_match = re.match("(r\d\d?).?", whole_reg_name)
                        if gp_match:
                            base_name = gp_match.group(1)
                        else:
                            base_name = whole_reg_name[-2:]
                        log.debug("Uses register {} base = {}".format(whole_reg_name, base_name))
                        r.append(base_name)
                    found = True
                    break
                else:
                    log.debug("Argument '{}' didn't match addressing mode {} ({})".format(a, am.re, regify(am.re)))

            if not found:
                log.error("Unknown addressing mode: {}".format(a))
                sys.exit(1)
        return r

    inputs = get_reg_ios(inst.ins);
    outputs = get_reg_ios(inst.outs);
    #print rat

    if cmdline.rename:
        renamed_inputs = ["pr{}".format(rat[r]) for r in inputs]
    else:
        renamed_inputs = inputs


    if cmdline.rename:
        for o in outputs:
            rat[o] = next_free_reg
            next_free_reg += 1
        renamed_outputs = ["pr{}".format(rat[r]) for r in outputs]
    else:
        renamed_outputs = outputs
    
    log.debug("Inputs are {} -> {}".format(" ".join(map(str, inputs)), " ".join(map(str,renamed_inputs))))
    log.debug("Outputs are {} -> {}".format(" ".join(map(str,outputs)), " ".join(map(str,renamed_outputs))))
    log.debug("RAT = {}".format(rat))

    log.debug("input depths:  {}".format(["{}:{}".format(x, dependence_depth.get(x,0)) for x in renamed_inputs]));
    log.debug("output depths: {}".format(["{}:{}".format(x, dependence_depth.get(x,0)) for x in renamed_outputs]));
    inst_depth = max([dependence_depth.get(x,0) for x in renamed_inputs] + 
                     [dependence_depth.get(x,0) for x in renamed_outputs] + 
                     [0])

    inst_depths[inst_depth] = inst_depths.get(inst_depth, []) + [inst_id]


    if cmdline.dot:
        dot_file.write("{} [label=\"{}: {}\"]\n".format(inst_id, inst_id, l.strip()))
               
    for i in zip(inputs, renamed_inputs):
        if last_writer.get(i[1]) is not None:
            if cmdline.dot:
                dot_file.write("{} -> {} [label=\"{} ({})\"]\n".format(last_writer[i[1]], inst_id,i[1], i[0]))
            log.debug("{} raw from to {}\n".format(l.strip(), r))

    for i in zip(outputs, renamed_outputs):
        if last_writer.get(i[1]) is not None:
            if cmdline.dot:
                dot_file.write("{} -> {} [label=\"{} ({})\", color=\"red\"]\n".format(last_writer[i[1]], inst_id,i[1], i[0]))
            log.debug("{} waw from to {}\n".format(l.strip(), r))

    for i in zip(outputs, renamed_outputs):
        if last_reader.get(i[1]) is not None:
            if cmdline.dot:
                dot_file.write("{} -> {} [label=\"{} ({})\", color=\"blue\"]\n".format(last_reader[i[1]], inst_id,i[1], i[0]))
            log.debug("{} war from to {}\n".format(l.strip(), r))

    for i in renamed_inputs:
        last_reader[i] = inst_id
        dependence_depth[i] = inst_depth
        log.debug("Updated depth of {} to {} beacuse of input".format(i, dependence_depth[i]))

    for r in renamed_outputs:
        dependence_depth[r] = inst_depth + 1
        log.debug("Updated depth of {} to {} beacuse of output".format(r, dependence_depth[r]))
        last_writer[r] = inst_id
        log.debug("{} wrote to {}\n".format(l.strip(), r))


    output.append([inst_id, l.strip(), inst_depth, " ".join(inputs), " ".join(outputs),  " ".join(renamed_inputs), " ".join(renamed_outputs)] + ["pr{}".format(rat[v]) for v in x86_registers])

    max_depth = max([max_depth, inst_depth])

output.append(["inst count", inst_count])
output.append(["critical path", max_depth])
output.append(["avg parallelism", (inst_count+0.0)/(max_depth+0.0)])
output.append(["physical regs used", next_free_reg])

if cmdline.dot:
    for k, v in inst_depths.items():
        dot_file.write("{{rank=same {}}}\n".format(" ".join(map(str,v))))
    dot_file.write("}")

if cmdline.csv:
    csv_file.write("\n".join(map(lambda x: ",".join(map(lambda x: '"{}"'.format(x), x)), output)))

sys.stdout.write(columnize(output, divider="|", headers=True))
