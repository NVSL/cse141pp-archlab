import logging as log
import json
import platform
import argparse
import sys
import os
import textwrap

def render_grades(results_json, full):
    r = ""
    for t in results_json['tests']:
        r +=f"{t['name']}\n\n"
        r +=f"\tMax score: {t['max_score']} \t Your score: {t['score']}\n\n"

            
    if (full) :
        k = map(lambda x: "\n".join(textwrap.wrap(x,10000)), t['output'].splitlines())
        #print(list(k))
        w = "\n".join(k)
        r+=textwrap.indent(w, "     ")

    return r

def main(argv=None):
    parser = argparse.ArgumentParser(description='Parse results.json')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('--file', default="results.json", help="which file to parse")
    parser.add_argument('--full', action="store_true", default=False, help="print out all the details")
    args = parser.parse_args(argv)
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.WARN)

    with open(args.file) as f:
        r = json.load(f)['gradescope_test_output']
        print(render_grades(r, args.full))

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
