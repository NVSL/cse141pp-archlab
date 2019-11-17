import os
import logging as log
import pytest
from . import pubsub_pull
from . import pubsub_push

required_env = ["PUBSUB_TOPIC",
                "GOOGLE_CLOUD_PROJECT",
                "PUBSUB_SUBSCRIPTION",
                "GOOGLE_APPLICATION_CREDENTIALS"]

class GooglePubSub(object):
    def __init__(self):
        if any(map(lambda x : x not in os.environ, required_env)):
            raise Exception(f"Can't start google pubsub withouth these environment variables: {required_env}")
    
    def pull(self):
        return pubsub_pull.pull()
        
    def push(self, job_id):
        return pubsub_push.push(job_id)

def test_pub_sub():

    if any(map(lambda x : x not in os.environ, required_env)):
        pytest.skip("Enivornment not configured")
    
    pubsub = GooglePubSub()
    
    pubsub.push(str(1))
    pubsub.push(str(2))
    pubsub.push(str(3))

    assert pubsub.pull() == str(1)
    assert pubsub.pull() == str(2)
    pubsub.push(str(4))
    assert pubsub.pull() == str(3)
    assert pubsub.pull() == str(4)
    
    assert pubsub.pull() == None
