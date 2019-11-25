#!/usr/bin/env python3

from .Runner import build_submission, run_submission_locally, run_submission_remotely, Submission, RunnerException, SubmissionResult
import logging as log
import json
import platform
import argparse
import sys
import os
import subprocess
import base64

class JSONPathException(Exception):
    pass
def extract(data, path):
    if len(path) == 0:
        return data

    if isinstance(data, dict):
        try:
            d = data[path[0]]
        except KeyError:
            raise JSONPathException("path not found")
        return extract(d, path[1:])
    elif isinstance(data, list):
        try:
            d = data[int(path[0])]
        except IndexError:
            raise JSONPathException("path not found")
        
        return extract(d, path[1:])
    else:
        raise JSONPathException("path not found")

def main(argv=None):
    parser = argparse.ArgumentParser(description='Run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('path', default=[], help="path components")

    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)

    d = json.loads(sys.stdin.read())

    try:
        r = extract(d, args.path)
    except JSONPathException:
        sys.stderr.write(f"Couldn't find path: {path}")
        sys.exit(1)
    else:
        print(r)
        sys.exit(0)
        
if __name__ == '__main__':
    main(sys.argv[1:])


def test_jextract():

    import pytest
    assert extract(json.loads("""{"a":"b"}"""), ["a"]) == "b"
    assert extract(json.loads("""["a","b"]"""), ["1"]) == "b"
    assert extract(json.loads("""["a","b"]"""), [1]) == "b"
    assert extract(json.loads("""["a",{"b":"c"}]"""), [1,"b"]) == "c"
    with pytest.raises(JSONPathException):
        extract(json.loads("""["a",{"b":"c"}]"""), [1,"b","c"])
    with pytest.raises(JSONPathException):
        extract(json.loads("""["a",{"b":"c"}]"""), [1,"e"])
    with pytest.raises(JSONPathException):
        extract(json.loads("""["a",{"b":"c"}]"""), [2,"e"])
    
    
    
