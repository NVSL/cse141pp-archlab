import os
import logging as log
from pathlib import Path
import pickle
from .BaseDataStore import BaseDataStore, do_test_datastore

class LocalDataStore(BaseDataStore):
    def __init__(self, namespace=None):
        super(LocalDataStore, self).__init__()
        self.directory = os.path.join(os.environ["EMULATION_DIR"],
                                      os.environ['GOOGLE_CLOUD_PROJECT'],
                                      "datastore",
                                      namespace if namespace is not None else os.environ["GOOGLE_RESOURCE_PREFIX"])
        os.makedirs(self.directory, exist_ok=True)

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

def test_local_data_store():
    do_test_datastore(LocalDataStore)
