import os
import logging as log
import pytest
import json
from google.cloud import datastore
import google.oauth2

class GoogleDataStore(object):
    def __init__(self):

        if "USE_ARCHLAB_TESTING_GOOGLE_ENVIRONMENT" in  os.environ:
            self.namespace =  os.environ['DATASTORE_NAMESPACE_TEST']
            self.credentials_path = os.environ['GOOGLE_CREDENTIALS_TEST']
        else:
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
    if "USE_ARCHLAB_TESTING_GOOGLE_ENVIRONMENT" not in os.environ:
        pytest.skip("Enivornment not configured")

    from .LocalDataStore import do_test

    ds = GoogleDataStore()

    do_test(ds)
