import platform
import argparse
import logging as log
from collections import OrderedDict
import sys
import math
import subprocess
import io
import tempfile

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
    parser.add_argument('--trace', required=True, help="trace file")
    parser.add_argument('--out', required=True, help="output png file")
    parser.add_argument('--range', default=":", help="lines to plot")
    
    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.WARN)

    cache = Cache(int(args.cache_size), int(args.line_size))

    start, stop = args.range.split(":")
    if start == "":
        start = 0
    else:
        start = int(start)
    if stop == "":
        stop = 1000000000000
    else:
        stop = int(stop)

    def plot_misses(cache, plot_data, lineum, line_addrs):
        misses = []
        for a in line_addrs:
            if cache.is_hit(a):
                misses.append("")
            else:
                misses.append(a)
        plot_data.write(",".join(map(str, [linenum]+line_addrs+misses))+ "\n")

    def plot_working_set(cache, plot_data, linenum, line_addrs):
        for k in cache.contents:
            plot_data.write(",".join(map(str,[linenum, k])) + "\n")

    log.debug(f"plotting {start}:{stop}")
    with tempfile.NamedTemporaryFile(mode="w") as plot_data:
        with tempfile.NamedTemporaryFile(mode="w") as working_set:
            linenum = 0
            with open(args.trace, "r") as file:
                while True:
                    if linenum < start:
                        continue
                    if linenum > stop:
                        break
                    linenum += 1
                    l = file.readline()
                    if l == "":
                        break

                    f = map(lambda x: int(x,0),l.split())
                    line_addrs = [k[1] for k in enumerate(f) if (k[0] % 2) == 1] # take every other field (i.e, the addresses)

                    plot_misses(cache, plot_data, linenum, line_addrs)
 #                   plot_working_set(cache, working_set, linenum, line_addrs)

                    for a in line_addrs:
                        cache.access_addr(a)

                    column_count = int(len(l.split())/2)

            gnuplot = subprocess.Popen(["gnuplot"], stdin=subprocess.PIPE)

            outfile = io.StringIO()

            outfile.write('set datafile separator ","\n')
            outfile.write('set terminal png\n')
            outfile.write(f'set output "{args.out}"\n')
            outfile.write(f"plot ")
#            outfile.write(f"'{working_set.name}' using 1:2 with points pt 7 ps 0.3 lc \"gray\",")
            for n in range(1, column_count + 1):
                outfile.write(f"'{plot_data.name}' using 1:{column_count + n + 1} with points pt 7 ps 0.3 lc \"red\",")
                outfile.write(f"'{plot_data.name}' using 1:{n + 1} with dots,")
                #outfile.write(f"'{args.out}' using 0:{column_count + n} with points pt 7 ps 0.5,")
                #outfile.write(f"'{args.out}' using 0:{n} with points pt 7 ps 0.1,")


            #outfile.write(f'\nset output "ws-{args.out}"\n')
            #outfile.write(f"plot ")

                #outfile.write(f"'{args.out}' using 0:{column_count + n} with points pt 7 ps 0.5,")
                #outfile.write(f"'{args.out}' using 0:{n} with points pt 7 ps 0.1,")
            outfile.write("\nquit\n")
            log.debug(outfile.getvalue())
            gnuplot.communicate(outfile.getvalue().encode("utf8"))

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

