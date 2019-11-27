import subprocess
import logging as log
import re
import argparse
import sys

def set_freq(target_MHz):
    try:
        subprocess.check_output(["cpupower", "frequency-set", "--freq", f"{target_MHz}MHz"]).decode("utf-8").split("\n")
        o = subprocess.check_output(["/usr/bin/cpupower", "frequency-info", "-w"]).decode("utf-8").split("\n")
        if f"{target_MHz}000" not in o[1]:
            raise Exception(f"Calling 'cpupower' to set frequency to {target_MHz}MHz failed: {o[1]}.")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Calling 'cpupower' to set frequency to {target_MHz}MHz failed: {e}")
    
def set_freq_cli(argv=None):
    parser = argparse.ArgumentParser(description='Set the CPU frequency')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('MHz', nargs=1, help="MHz to use. 'max' for maximum available.")

    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
              
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)
    log.debug(f"Command line args: {args}")

    if args.MHz[0] == "max":
        target_MHz=get_freqs()[0]
    else:
        target_MHz=int(args.MHz[0])
    set_freq(target_MHz)
    
def get_freqs():
    try:
        if subprocess.call(['which', 'cpupower'], stdout=subprocess.PIPE) != 0:
            log.warning("cpupower utility is not available.  Clock speed setting will not work.")

        try:
            o = subprocess.check_output(["cpupower", "frequency-info", "-s"]).decode("utf-8").split("\n")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Calling 'cpupower' to extract frequency list failed: {e}")

        if "analyzing CPU" not in o[0]:
            raise Exception("Error running cpu power to extract available frequencies")
        fields = o[1].split(", ")
        frequencies = []
        for f in fields:
            m = re.search("(\d+):(\d+)", f)
            if not m:
                raise Exception(f"Failed to parse output from cpupower: {f}")
            f = int(int(m.group(1))/1000)
            if f % 10 == 0: # Sometimes the list includes things like 2001Mhz, but they don't seem to actually valid values, so trim them.
                frequencies.append(f)
    except Exception as e:
        frequencies=[]

    return frequencies

def get_freqs_cli(argv=None):
    parser = argparse.ArgumentParser(description='Get the list of available CPU frequencies.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")

    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
              
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)
    log.debug(f"Command line args: {args}")

    frequencies=get_freqs()
    print(f"export ARCHLAB_AVAILABLE_CPU_FREQUENCIES=\"{' '.join(map(str, frequencies))}\"")
    
    
