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
parser.add_argument('--font', default="Courier-bold", help="Font to use in graph output")
parser.add_argument('--font-size', default="16", help="Font size to use in graph output")
parser.add_argument('--shape', default="record", help="Font size to use in graph output")
parser.add_argument('--linear', default=False, action='store_true', help="Linearize graph output")
parser.add_argument('--edge-width', default=2, help="Width of drawn edges")
parser.add_argument('--pin-trace', action='store_true', help="Process a pin trace instead of asm")

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


AddrMode = namedtuple("AddrMode", "re ex count")

if cmdline.pin_trace:
    x86_any_reg = "((|e|r)({}))d?".format("|".join(x86_registers))
    addr_prefix = "(?:\w+ )?ptr "
    x86_addressing_modes = [
        AddrMode("\({reg}\)", "(%rax)", 1),
        AddrMode("0x[0-9A-F]+", "0x1234F", 0),
        AddrMode("-?\d+", "12345", 0),
        AddrMode("\({reg},{reg}\)", "(%rax,%rax)", 2),
        AddrMode("{reg}:\({reg},{reg}\)", "%fs:(%rax,%rax)", 3),

        AddrMode(addr_prefix + "\[{reg}\+0x[0-9A-F]+\]", "qword ptr [rsp+1234]", 1),
        AddrMode("{reg}", "rax", 1),
        AddrMode(addr_prefix + "\[{reg}\+{reg}\*\d+\]", "ptr [rdi+rsi*i]", 2),
    ]
else:
    x86_any_reg = "\%((|e|r)({}))d?".format("|".join(x86_registers))
    x86_addressing_modes = [
        AddrMode("\({reg}\)", "(%rax)", 1),
        AddrMode("{reg}", "%rax", 1),
        AddrMode("\$-?\d+", "$12345", 0),
        AddrMode("-?\d+", "12345", 0),
        AddrMode("-?\d+\({reg}\)", "12345(%rax)", 1),
        AddrMode("\({reg},{reg}\)", "(%rax,%rax)", 2),
        AddrMode("{reg}:\({reg},{reg}\)", "%fs:(%rax,%rax)", 3),
    ]

    
class Inst(object):
    def __init__(self, name, ins, outs, ignore=None, is_branch=False, arg_count=None):
        self.name = name
        self.ins = ins
        self.outs = outs
        self.is_branch = is_branch
        if ignore is None:
            ignore = []
        if arg_count is None:
            self.arg_count = len(set(filter(lambda x: isinstance(x, int), ins + outs + ignore)))
        else:
            self.arg_count = arg_count
        log.debug("defined inst: {} {} {} {}".format(name, ins, outs, self.arg_count))

    

def arith(x, op, set_flags=False): 
    return Inst(x, ins=[0, 1], outs=[1] + (["flags"] if set_flags else []))

def branch(x):
    return Inst(x, ins=[0, "flags"], outs=[], is_branch=True)

x86_instructions = [
    arith("add", "+"),
    arith("xor", "^"),
    arith("or", "^"),
    arith("imul", "*"),
    arith("sub", "-", set_flags=True),
    arith("and", "&"),
    arith("shl", "<<"),
    arith("sal", "<<"),
    arith("shr", ">>"),
    arith("sar", "<<"),
    Inst("nop", ins=[], outs=[], arg_count=2),
    Inst("call", ins=[0], outs=[]),
    Inst("clt", ins=["ax"], outs=["ax"]),
    Inst("sar", ins=[0], outs=[0]),
    Inst("neg", ins=[0], outs=[0]),
    Inst("imul", ins=[0], outs=["dx", "ax"]),
    Inst("cmp", ins=[0,1], outs=["flags"]),
    Inst("inc", ins=[0], outs=[0]),
    Inst("test", ins=[0,1], outs=["flags"]),
    Inst("lea", ins=[0], outs=[1]),
    Inst("mov", ins=[0], outs=[1]),
    Inst("movslq", ins=[0], outs=[1]),
    Inst("movsl", ins=[0], outs=[1]),
    branch("jne"),
    branch("jnz"),
    branch("jz"),
    branch("jle"),
    branch("jbe"),
    branch("jl"),
    branch("je"),
    branch("jae"),
    branch("jg"),
    branch("jge"),
    Inst("cmovne", ins=["flags", 0], outs=[1]),
    Inst("jmp", ins=[0], outs=[], is_branch=True),
    Inst("pop", ins=["sp"], outs=[0, "sp"]),
    Inst("push", ins=[0, "sp"], outs=["sp"]),
    Inst("ret", ins=["ax"], outs=[], is_branch=True),
    Inst("ret", ins=[0], outs=[], is_branch=True),
    Inst("j", ins=[0], outs=[], is_branch=True),
]

def regify(x):
    return "^{}$".format(x.format(reg=x86_any_reg))


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
    dot_file.write("digraph trace { pad=0; margin=0; bgcolor=\"#00000000\"")

output = []
output.append(["line num", "code", "depth", "ins", "outs", "renamed_ins", "renamed_outs"] + x86_registers)


inst_id = 0 
inst_count = 0 
max_depth = 1
inst_ids = []
last_branch = 0
branch_depth = 0
last_instruction = 0

for l in lines:
    log.debug("Analyzing {}".format(l))
    inst_id += 1
    inst_ids += [inst_id]
    
    l = re.sub("\#.*", "", l) # trim comments
    l = re.sub("^%", "", l) # Trim pin trace lines


    discard_patterns = [
        "file format",
        "Disassembly",
        "unknown",
        "^\s*\.\w+.*",
        "^\s*\w+:.*",
        "^\s*\.",
        "\.\.\."]
    skip = False

    for p in discard_patterns:
        if re.search(p, l):
            skip = True
            log.debug("Skipping '{}' because it matches '{}'".format(l.strip(), p))
            break
    if skip:
        continue

    if re.match("^\s*$", l):
        log.debug("Skipping empty line: '{}'".format(l))
        continue
    
    # match a line of x86 assembly.
    g = re.match("\s*(\w+)(.*)", l)
    if not g:
        log.error("Malformed line: {}".format(l))
        sys.exit(1)
        continue
    inst_count += 1
    log.debug("Found x86 instructions (line {}): {}\n".format(inst_id, l.strip()))

    args = g.group(2).split(", ");
    args = [s.strip() for s in args if s.strip() != ""]
    
    assert len(args) <= 4, "Too many argument: {} has {}".format(l, len(args))
    op = g.group(1)

    if not cmdline.pin_trace:
        #Trim word size suffixes. don't cut suffixes off of jumps
        if op[-1:] in ['b', 's', 'w', 'l', 'd', 'q'] and op[0:1] != "j" and op != "call":
            op = op[0:-1]

    inst = x86_inst_map.get((op, len(args)))
    if not inst:
        log.error("Unknown instruction: '{}' ({} args: {}) on line {}".format(op, len(args), args, l))
        sys.exit(1)

    log.debug("Using {} with {} args".format(inst.name, inst.arg_count))
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
                log.debug("Checking {} againsnt {}\n".format(a, am.re))
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


    inst_depth_candidates = ([dependence_depth.get(x,0) for x in renamed_inputs] + 
                             [dependence_depth.get(x,0) for x in renamed_outputs] +
                             [branch_depth] +
                             [0])
    log.debug("Inst depth input candidates are {}".format([dependence_depth.get(x,0) for x in renamed_inputs]))
    log.debug("Inst depth output candidates are {}".format([dependence_depth.get(x,0) for x in renamed_outputs]))
    log.debug("Inst depth branch depth candidate is {}".format(branch_depth))

    inst_depth = max(inst_depth_candidates)
    log.debug("Inst depth is {}".format(inst_depth))

    if inst.is_branch:
        branch_depth = inst_depth + 1
        log.debug("Increasing branch depth to {}".format(branch_depth))
    


    inst_depths[inst_depth] = inst_depths.get(inst_depth, []) + [inst_id]
    log.debug("Updated inst_depth[{}] = {}".format(inst_depth, inst_depths.get(inst_depth)))

    if cmdline.dot:
        dot_file.write("{} [label=\"{}: {}\", fontsize=\"{}\", fontname=\"{}\", shape=\"{}\"]\n".format(inst_id,
                                                                                                                   inst_id,
                                                                                                                   l.strip(),
                                                                                                                   cmdline.font_size,
                                                                                                                   cmdline.font,
                                                                                                                   cmdline.shape))
               
    for i in zip(inputs, renamed_inputs):
        if last_writer.get(i[1]) is not None:
            if cmdline.dot:
                dot_file.write("{} -> {} [label=\"{}{}\", color=\"black\", fontsize=\"{}\", fontname=\"{}\",penwidth={}]\n".format(last_writer[i[1]], inst_id, i[1], " ({})".format(i[0]) if i[0] != i[1] else "", cmdline.font_size, cmdline.font, cmdline.edge_width))
            log.debug("{} raw from to {}\n".format(l.strip(), r))

    for i in zip(outputs, renamed_outputs):
        if last_writer.get(i[1]) is not None:
            if cmdline.dot:
                dot_file.write("{} -> {} [label=\"{}{}\", color=\"red\", fontsize=\"{}\", fontname=\"{}\",penwidth={}]\n".format(last_writer[i[1]], inst_id,i[1],  " ({})".format(i[0]) if i[0] != i[1] else "", cmdline.font_size, cmdline.font, cmdline.edge_width))
                log.debug("{} waw from to {}\n".format(l.strip(), r))

    for i in zip(outputs, renamed_outputs):
        if last_reader.get(i[1]) is not None:
            if cmdline.dot:
                dot_file.write("{} -> {} [label=\"{}{}\", color=\"blue\", fontsize=\"{}\", fontname=\"{}\",penwidth={}]\n".format(last_reader[i[1]], inst_id,i[1],  " ({})".format(i[0]) if i[0] != i[1] else "", cmdline.font_size, cmdline.font, cmdline.edge_width))
            log.debug("{} war from to {}\n".format(l.strip(), r))

    if inst.is_branch and last_branch != 0:
        if cmdline.dot:
            dot_file.write("{} -> {} [label=\"{}\", color=\"gray\", fontsize=\"{}\", fontname=\"{}\",penwidth={}]\n".format(last_branch, inst_id, "PC", cmdline.font_size, cmdline.font, cmdline.edge_width))

    if last_branch != 0 and last_branch == last_instruction:
        if cmdline.dot:
            dot_file.write("{} -> {} [label=\"{}\", color=\"gray\", fontsize=\"{}\", fontname=\"{}\",penwidth={}]\n".format(last_branch, inst_id, "PC", cmdline.font_size, cmdline.font, cmdline.edge_width))

    if inst.is_branch:
        last_branch = inst_id
        log.debug("Last branch is now  {}".format(last_branch))
    
            
    for i in renamed_inputs:
        last_reader[i] = inst_id
        dependence_depth[i] = inst_depth
        log.debug("Updated depth of reg {} to {} beacuse of input".format(i, dependence_depth[i]))

    for r in renamed_outputs:
        dependence_depth[r] = inst_depth + 1
        log.debug("Updated depth of reg {} to {} beacuse of output".format(r, dependence_depth[r]))
        last_writer[r] = inst_id
        log.debug("{} wrote to {}\n".format(l.strip(), r))


    output.append([inst_id, l.strip(), inst_depth, " ".join(inputs), " ".join(outputs),  " ".join(renamed_inputs), " ".join(renamed_outputs)] + ["pr{}".format(rat[v]) for v in x86_registers])
    
    max_depth_candidates = [max_depth, inst_depth, branch_depth if inst.is_branch else 0]
    log.debug("Max depth candidates: {}".format(max_depth_candidates))
    max_depth = max(max_depth_candidates)
    log.debug("Increasing max depth to {}.".format(max_depth))

    last_instruction = inst_id
max_depth += 1 # max_depth counts edges.  We actually need instructions.

output.append(["inst count", inst_count])
output.append(["critical path", max_depth])
output.append(["avg parallelism", (inst_count+0.0)/(max_depth+0.0)])
output.append(["physical regs used", next_free_reg])

if cmdline.dot:
    if cmdline.linear:
        dot_file.write("{} [style=invisible, arrowsize=0]\n".format("->".join(map(str, inst_ids))))
    else:
        for k, v in inst_depths.items():
            dot_file.write("{{rank=same {}}}\n".format(" ".join(map(str,v))))
    dot_file.write("}")

if cmdline.csv:
    csv_file.write("\n".join(map(lambda x: ",".join(map(lambda x: '"{}"'.format(x), x)), output)))

sys.stdout.write(columnize(output, divider="|", headers=True))
