import os
import logging as log
import pytest
from google.cloud import pubsub_v1
import google.oauth2
import google.api_core
from uuid import uuid4 as uuid    
class GooglePubSub(object):
    def __init__(self, private_subscription=False, subscription_base=None):

        if subscription_base is None:
            self.subscription_base =  os.environ['PUBSUB_SUBSCRIPTION']
        else:
            self.subscription_base = subscription_base
            
        if private_subscription:
            self.subscription_name = fr"{self.subscription_base}-{str(uuid())}"
        else:
            self.subscription_name = self.subscription_base
            
        self.topic = os.environ['PUBSUB_TOPIC']
        self.credentials_path = os.environ['GOOGLE_CREDENTIALS']

        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        
        
        assert os.path.exists(self.credentials_path)
        self.credentials = google.oauth2.service_account.Credentials.from_service_account_file(self.credentials_path)
        self.subscriber = pubsub_v1.SubscriberClient(credentials=self.credentials)
        self.subscription_path = self.subscriber.subscription_path(self.project, self.subscription_name)
        self.publisher = pubsub_v1.PublisherClient(credentials=self.credentials)
        self.topic_name = self.publisher.topic_path(self.project, self.topic)

        if private_subscription:
            self.subscription = self.subscriber.create_subscription(self.subscription_path, self.topic_name)
        log.debug(f"pubsub credentials path={self.credentials_path}")
#        log.debug(f"env credentials path={os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
        log.debug(f"pubsub topic_name ={self.topic_name}")
        log.debug(f"pubsub subscription name={self.subscription_path}")

        
    def pull(self):

        try:
            response = self.subscriber.pull(self.subscription_path, max_messages=1)
        except google.api_core.exceptions.DeadlineExceeded:
            return None

        if len(response.received_messages) > 0:
            for msg in response.received_messages:
                payload = msg.message.data.decode("utf8")
                log.debug(f"Received {payload}")
                self.subscriber.acknowledge(self.subscription_path, [msg.ack_id])
            return payload
        else:
            return None
        
    def push(self, job_id):

        log.debug(f"Publishing to {self.topic_name}")
        t = self.publisher.publish(
            self.topic_name,
            job_id.encode("utf8")
        )
        log.debug(f"Result = {t.result()}")


    def tear_down(self):
        self.subscriber.delete_subscription(self.subscription_path)
        
def test_push():

    from .LocalPubSub import do_test
    
    if os.environ.get('DEPLOYMENT_MODE', "EMULATION") in ["EMULATION", ""]:
        pytest.skip("In emulation mode")

    
    from .CloudServices import GetPubSub
    PubSub = GetPubSub()


    pubsub = PubSub(private_subscription=True)
    try:
        do_test(pubsub)
    except:
        pubsub.teardown()
