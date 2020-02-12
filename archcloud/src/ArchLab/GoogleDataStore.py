import os
import logging as log
import pytest
from google.cloud import datastore
import google.oauth2
import datetime
import pytz

from .BaseDataStore import BaseDataStore, do_test_datastore

class GoogleDataStore(BaseDataStore):
    def __init__(self, namespace=None):
        super(GoogleDataStore, self).__init__()
        self.namespace = namespace if namespace is not None else os.environ['GOOGLE_RESOURCE_PREFIX']
        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        self.datastore_client = datastore.Client(project=self.project,
                                                 namespace=self.namespace)
        self.kind = "ArchLabJob"

    def alloc_job(self, job_id):
        job_key = self.datastore_client.key(self.kind, job_id)
        job = datastore.Entity(key=job_key, exclude_from_indexes=['status_reasons', 'submission_status_reasons'])
        job['job_id'] = job_id
        return job

    def put_job(self, job):
        # import traceback
        # for line in traceback.format_stack():
        #     log.debug(line.strip())
        log.debug(f"Putting job {job['job_id']}: {job}")
        self.datastore_client.put(job)

    def get_job(self, job_id):
        # import traceback
        # for line in traceback.format_stack():
        #     log.debug(line.strip())

        query = self.datastore_client.query(kind=self.kind)
        query.add_filter('job_id', '=', job_id)
        query_iter = query.fetch()
        for entity in query_iter:
            log.debug(f"Getting job {job_id}: {entity}")
            return entity        

    def query_iterator(self, **kwargs):
        log.debug(f"querying with {kwargs}")
        query = self.datastore_client.query(kind=self.kind)
        limit = kwargs.get('limit',None)
        kwargs.pop('limit', None)
        
        for k,v in kwargs.items():
            query.add_filter(k, '=', v)
        query_iter = query.fetch(limit=limit)
        return query_iter
    
    def query(self, **kwargs):
        return list(self.query_iterator(**kwargs))

    def get_recently_completed_jobs(self, seconds_ago):
        query = self.datastore_client.query(kind=self.kind)
        query.add_filter('submitted_utc', ">", datetime.datetime.now(pytz.utc) - datetime.timedelta(seconds = seconds_ago))            
        query_iter = query.fetch()
        r =  list(filter(lambda x: x['status'] == "COMPLETED", query_iter))
        log.debug(f"found {len(r)} recently completed jobs")
        return r

        
def test_google_data_store():
    do_test_datastore(GoogleDataStore)
