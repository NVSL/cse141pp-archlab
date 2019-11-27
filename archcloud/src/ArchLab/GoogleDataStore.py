import os
import logging as log
import pytest
import json
from google.cloud import datastore
import google.oauth2

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
	     metadata, 
	     job_submission_json, 
	     manifest,
	     output,
	     status
    ):
        
        job_key = self.datastore_client.key(self.kind, job_id)
        job = datastore.Entity(key=job_key, exclude_from_indexes=('metadata', 'job_submission_json', 'manifest', 'output'))
        job['job_id'] = job_id
        job['metadata'] = metadata
        job['job_submission_json'] = job_submission_json
        job['manifest'] = manifest
        job['output'] = output
        job['status'] = status

        self.datastore_client.put(job)


        
def test_google_data_store():
    if os.environ.get('DEPLOYMENT_MODE', "EMULATION") in ["EMULATION", ""]:
        pytest.skip("In emulation mode")

    from .LocalDataStore import do_test
    
    from .CloudServices import GetDS
    DS = GetDS()

    assert DS == GoogleDataStore
    
    ds = DS()

    do_test(ds)
