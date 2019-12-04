import os
import logging as log
import pytest
import json
from google.cloud import datastore
import google.oauth2
import datetime
import platform
import pytz

class GoogleDataStore(object):
    def __init__(self):

        self.namespace =  os.environ['DATASTORE_NAMESPACE']
        self.credentials_path = os.environ['GOOGLE_CREDENTIALS']

        self.project = os.environ['GOOGLE_CLOUD_PROJECT']

        log.debug(f"opening {self.credentials_path}")
        self.credentials = google.oauth2.service_account.Credentials.from_service_account_file(self.credentials_path)
        self.datastore_client = datastore.Client(project=self.project,
                                                 namespace=self.namespace,
                                                 credentials=self.credentials)
        self.kind = os.environ['DATASTORE_OBJECT_KIND']
                
    def pull(self, job_id):
        query = self.datastore_client.query(kind=self.kind)
        query.add_filter('job_id', '=', job_id)
        query_iter = query.fetch()
        for entity in query_iter:
            return entity

    def query(self, **kwargs):
        log.debug(f"querying with {kwargs}")
        query = self.datastore_client.query(kind=self.kind)
        for k,v in kwargs.items():
            query.add_filter(k, '=', v)
        query_iter = query.fetch()
        return list(query_iter)

    def push(self,
	     job_id,
	     job_submission_json, 
	     output,
	     status
    ):
        job_key = self.datastore_client.key(self.kind, job_id)
        job = datastore.Entity(key=job_key, exclude_from_indexes=('job_submission_json',))
        job['job_id'] = job_id
        job['job_submission_json'] = job_submission_json
        job['status'] = status
        job['submission_status'] = ""
        job['submitted_utc'] = datetime.datetime.now(pytz.utc)
        job['started_utc'] = ""
        job['completed_utc'] = ""
        job['submitted_host'] = platform.node()
        job['runner_host'] = ""
        
        self.datastore_client.put(job)

    def update(self,
	       job_id,
	       **kwargs):
        job = self.pull(job_id)
        job.update(**kwargs)
        self.datastore_client.put(job)

    def get_recently_completed_jobs(self, seconds_ago):
        query = self.datastore_client.query(kind=self.kind)
        query.add_filter('submitted_utc', ">", datetime.datetime.now(pytz.utc) - datetime.timedelta(seconds = seconds_ago))            
        query_iter = query.fetch()
        r =  list(filter(lambda x: x['status'] == "COMPLETED", query_iter))
        log.debug(f"found {len(r)} recently completed jobs")
        return r

        
def test_google_data_store():
    if os.environ.get('DEPLOYMENT_MODE', "EMULATION") in ["EMULATION", ""]:
        pytest.skip("In emulation mode")

    from .LocalDataStore import do_test
    
    from .CloudServices import GetDS
    DS = GetDS()

    assert DS == GoogleDataStore
    
    ds = DS()

    do_test(ds)
