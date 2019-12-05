import os
import logging as log
from pathlib import Path
import pytest
import pickle
import json
import tempfile
import datetime
import platform
import pytz

class BaseDataStore(object):
    def alloc_job(self, job_id):
        raise NotImplemented
    
    def get_job(self, job_id):
        raise NotImplemented
    
    def put_job(self,job):
        raise NotImplemented
    
    def push(self,
	     job_id,
	     job_submission_json, 
	     output,
	     status
    ):
        job = self.alloc_job(job_id)

        job['job_submission_json'] = job_submission_json
        job['status'] = status
        job['submission_status'] = ""
        job['submitted_utc'] = datetime.datetime.now(pytz.utc)
        job['started_utc'] = ""
        job['completed_utc'] = ""
        job['submitted_host'] = platform.node()
        job['runner_host'] = ""

        self.put_job(job)

    def update(self,
	       job_id,
	       **kwargs):
        job = self.pull(job_id)
        job.update(**kwargs)
        self.put_job(job)

    def pull(self, job_id):
        return self.get_job(job_id)
                

class LocalDataStore(BaseDataStore):
    def __init__(self, directory = None):
        super(LocalDataStore, self).__init__()
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
            with open(p, 'rb') as f:
                job = pickle.load(f)
                log.debug(f"read {job}")
                if len(kwargs) == 0 or all(map(lambda kv: job[kv[0]] == kv[1], kwargs.items())):
                    log.debug("It matched!")
                    r.append(job)
                else:
                    log.debug("It didn't match")
        return r

    def alloc_job(self, job_id):
        return dict(job_id=job_id)
    
    def get_job(self, job_id):
        path = os.path.join(self.directory, str(job_id))
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except:
            return None

    def put_job(self, job):
        path = os.path.join(self.directory, job['job_id'])
        with open(path, "wb") as f:
            pickle.dump(job, f)


def do_test(ds):
    from uuid import uuid4 as uuid
    import json
    import time
    id1 = uuid()
    id2 = uuid()
    junk = str(uuid())
    log.debug(f"Junk = {junk}")
    ds.push(job_id = str(id1),
            job_submission_json=json.dumps([]),
            output="out",
            status=junk)
    ds.push(job_id = str(id2),
            job_submission_json=json.dumps({}),
            output="out",
            status=junk)
    time.sleep(1)
    assert ds.pull(str(uuid())) == None

    ds.update(job_id = str(id2),
              foo="d")
    time.sleep(1)
    assert ds.pull(str(id2))['foo'] == "d"

    ds.pull(str(id2))['submitted_utc'] - datetime.datetime.now(pytz.utc)
    
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
    
