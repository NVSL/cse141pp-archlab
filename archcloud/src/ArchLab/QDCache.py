import platform
import argparse
import logging as log
from collections import OrderedDict
import sys
import math

class Cache(object):
    def __init__(self, capacity, line_size):
        self.capacity = 1024*capacity
        self.line_size = line_size

        self.contents = OrderedDict()

    def compute_line_addr(self, x):
        return math.floor(int(x)/self.line_size) * self.line_size

    def is_hit(self, addr):
        line = self.compute_line_addr(addr)
        return line in self.contents

    def access_addr(self, addr):
        line = self.compute_line_addr(addr)
        if self.is_hit(line):
            del self.contents[line]
        else:
            if len(self.contents) > self.capacity/self.line_size:
                self.contents.popitem(last=False)
        self.contents[line] = True
        
def main(argv=None):
    parser = argparse.ArgumentParser(description='Trivial cache simulator')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('--cache-size', default="32", help="Cache size (in kB)")
    parser.add_argument('--line-size', default="64", help="Cache line size (in B)")
    parser.add_argument('trace', default="-", help="trace file")
    parser.add_argument('--out', required=True, help="output file")
    
    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.WARN)

    cache = Cache(int(args.cache_size), int(args.line_size))

    with open(args.out, "w") as out:
        with open(args.trace, "r") as file:
            while True:
                l = file.readline()
                if l == "":
                    break

                f = map(lambda x: int(x,0),l.split())
                line_addrs = [k[1] for k in enumerate(f) if (k[0] % 2) == 1] # take every other field (i.e, the addresses)
                misses = []
                for a in line_addrs:
                    if cache.is_hit(a):
                        misses.append("")
                    else:
                        misses.append(a)
                    cache.access_addr(a)

                out.write(",".join(map(str, line_addrs+misses))+ "\n")
                column_count = int(len(l.split())/2)

    with open("plot.gnuplot", "w") as outfile:
        outfile.write('set datafile separator ","\n')
        outfile.write(f"plot ")
        for n in range(1, column_count + 1):
            outfile.write(f"'{args.out}' using 0:{column_count + n} with points pt 7 ps 0.3 lc \"red\",")
            outfile.write(f"'{args.out}' using 0:{n} with dots,")
            #outfile.write(f"'{args.out}' using 0:{column_count + n} with points pt 7 ps 0.5,")
            #outfile.write(f"'{args.out}' using 0:{n} with points pt 7 ps 0.1,")
        outfile.write("\n")
        
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

