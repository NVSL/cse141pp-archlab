import os
import logging as log
from pathlib import Path
import pytest
import json
import tempfile

class LocalDataStore(object):
    def __init__(self, directory = None):
        if directory == None:
            if "DATA_STORE_DIR" in os.environ:
                directory = os.environ["DATA_STORE_DIR"]
            else:
                self.tmp_dir = tempfile.TemporaryDirectory()
                directory = self.tmp_dir.name

        self.directory = directory

        if not os.path.exists(self.directory):
            log.debug(f"Creating inbox: {self.directory}")
            os.mkdir(self.directory)

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
    id1 = uuid()
    id2 = uuid()
    ds.push(job_id = str(id1),
            metadata="a",
            job_submission_json=json.dumps([]),
            manifest="a file",
            output="out",
            status="sudmitted")
    ds.push(job_id = str(id2),
            metadata="b",
            job_submission_json=json.dumps({}),
            manifest="b file",
            output="out2",
            status="sudmitted2")

    assert ds.pull(str(id1))['metadata'] == "a"
    assert ds.pull(str(id2))['manifest'] == "b file"
    assert ds.pull(str(uuid())) == None


def test_local_data_store():

    tmp_dir = tempfile.TemporaryDirectory()
    do_test(LocalDataStore(tmp_dir.name))

    do_test(LocalDataStore())
    td = tempfile.TemporaryDirectory(prefix="ENVIRON")
    os.environ['DATA_STORE_DIR'] = td.name
    ds = LocalDataStore()
    assert ds.pull(1) == None

    do_test(ds)
    assert "ENVIRON" in ds.directory
    
