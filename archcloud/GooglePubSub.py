import os
import logging as log
import pytest
import pubsub_pull
import pubsub_push

class GooglePubSub(object):
    def __init__(self, directory):
        pass
    
    def pull(self):
        return pubsub_pull.pull()
        
    def push(self, job_id):
        return pubsub_push.push(job_id)

def test_pub_sub():
    
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
