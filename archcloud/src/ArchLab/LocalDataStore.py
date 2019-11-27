import os
import logging as log
from pathlib import Path
import pytest
import json
import tempfile

class LocalDataStore(object):
    def __init__(self, directory = None):
        if directory == None:
            if "EMULATION_DIR" in os.environ:
                directory = os.environ["EMULATION_DIR"]
            else:
                self.tmp_dir = tempfile.TemporaryDirectory()
                directory = self.tmp_dir.name

        self.directory = os.path.join(directory, "ds")

        if not os.path.exists(self.directory):
            log.debug(f"Creating inbox: {self.directory}")
            os.mkdir(self.directory)

    def query(self, **kwargs):
        log.debug(f"querying with {kwargs}")
        r = []
        for p in Path(self.directory).iterdir():
            log.debug(f"examining {p}")
            with open(p, 'r') as f:
                job = json.loads(f.read())
                log.debug(f"read {job}")
                if len(kwargs) == 0 or all(map(lambda kv: job[kv[0]] == kv[1], kwargs.items())):
                    log.debug("It matched!")
                    r.append(job)
                else:
                    log.debug("It didn't match")
        return r
    
    def pull(self, job_id):
        path = os.path.join(self.directory, str(job_id))
        try:
            with open(path, "r") as f:
                return json.loads(f.read())
        except:
            return None

    def push(self,
             job_id,
	     metadata, 
             job_submission_json, 
	     manifest,
	     output,
	     status):
        job={}
        job['job_id'] = job_id
        job['metadata'] = metadata
        job['job_submission_json'] = job_submission_json
        job['manifest'] = manifest
        job['output'] = output
        job['status'] = status

        path = os.path.join(self.directory, str(job_id))
        with open(path, "w") as f:
            f.write(json.dumps(job))

def do_test(ds):
    from uuid import uuid4 as uuid
    import time
    id1 = uuid()
    id2 = uuid()
    junk = str(uuid())
    log.debug(f"Junk = {junk}")
    ds.push(job_id = str(id1),
            metadata="a",
            job_submission_json=json.dumps([]),
            manifest="a file",
            output="out",
            status=junk)
    ds.push(job_id = str(id2),
            metadata="b",
            job_submission_json=json.dumps({}),
            manifest="b file",
            output="out",
            status=junk)
    time.sleep(1)
    assert ds.pull(str(id1))['metadata'] == "a"
    assert ds.pull(str(id2))['manifest'] == "b file"
    assert ds.pull(str(uuid())) == None

    r = ds.query(job_id=str(id1))
    assert len(r) == 1
    assert r[0]['job_id'] == str(id1)

    r = ds.query(status=junk)
    assert len(r) == 2

def test_local_data_store():
    try:
        del os.environ['EMULATION_DIR']
    except:
        pass

    os.environ['DEPLOYMENT_MODE'] = "EMULATION"

    from .CloudServices import GetDS
    DS = GetDS()

    assert DS == LocalDataStore
    
    tmp_dir = tempfile.TemporaryDirectory()
    do_test(DS(tmp_dir.name))

    do_test(DS())
    td = tempfile.TemporaryDirectory(prefix="ENVIRON")
    os.environ['EMULATION_DIR'] = td.name
    ds = DS()
    assert ds.pull(1) == None

    do_test(ds)
    assert "ENVIRON" in ds.directory
    
