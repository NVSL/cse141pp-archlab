import logging as log
import datetime
import pytz
import platform

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
                
def do_test_datastore(DataStoreType):
    ds = DataStoreType(namespace="testing-junk")

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
