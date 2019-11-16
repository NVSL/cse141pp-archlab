import os
import logging as log
import pytest
import json


import datastore_pull
import datastore_push

class GoogleDataStore(object):
    def __init__(self):
        pass
    def pull(self, key):
        return datastore_pull.pull(key)
    def push(self, *argc):
        return datastore_push.push(*argc)
            
def test_data_store():
    from uuid import uuid4 as uuid    
    ds = GoogleDataStore()
    id1 = uuid()
    ds.push(job_id = id1,
            metadata="a",
            job_submission_json=json.dumps([]),
            manifest="a file",
            output="out",
            status="sudmitted")
    ds.push(job_id = id2,
            metadata="b",
            job_submission_json=json.dumps({}),
            manifest="b file",
            output="out2",
            status="sudmitted2")

    assert ds.pull(id1)['metadata'] == "a"
    assert ds.pull(id2)['manifest'] == "b file"
    assert ds.pull(uuid()) == None
