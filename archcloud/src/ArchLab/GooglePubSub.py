import os
import logging as log
import pytest
from google.cloud import pubsub_v1
import google.oauth2
import google.api_core

class GooglePubSub(object):
    def __init__(self):

        self.subscription =  os.environ['PUBSUB_SUBSCRIPTION']
        self.topic = os.environ['PUBSUB_TOPIC']
        self.credentials_path = os.environ['GOOGLE_CREDENTIALS']

        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        
        
        assert os.path.exists(self.credentials_path)
        self.credentials = google.oauth2.service_account.Credentials.from_service_account_file(self.credentials_path)
        self.subscriber = pubsub_v1.SubscriberClient(credentials=self.credentials)
        self.subscription_path = self.subscriber.subscription_path(self.project, self.subscription)
        self.publisher = pubsub_v1.PublisherClient(credentials=self.credentials)
        self.topic_name = self.publisher.topic_path(self.project, self.topic)
        log.debug(f"pubsub credentials path={self.credentials_path}")
        log.debug(f"env credentials path={os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
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

    
def test_push():

    from .LocalPubSub import do_test
    
    if os.environ.get('DEPLOYMENT_MODE', "EMULATION") == "EMULATION":
        pytest.skip("In emulation mode")

    pubsub = GooglePubSub()

    do_test(pubsub)
