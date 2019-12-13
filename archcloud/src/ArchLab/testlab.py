import sys
import argparse
import platform
from .Runner import LabSpec
import subprocess

import logging as log

def main(argv=None):
    parser = argparse.ArgumentParser(description='Test a lab.')
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Be verbose")
    parser.add_argument('--fail-fast', action='store_true', default=False, help="stop on first error")
    args = parser.parse_args(sys.argv[1:])
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if True else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    p = subprocess.Popen(['runlab.d'])
    lab = LabSpec.load(".")
    r = lab.run_meta_regressions(failfast=args.fail_fast)
    p.kill()
    p.wait()
    return r
    
if __name__ == '__main__':
    main(sys.argv[1:])
