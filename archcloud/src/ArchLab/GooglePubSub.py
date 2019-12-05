import os
import logging as log
import pytest
from google.cloud import pubsub_v1
import google.oauth2
import google.api_core
from uuid import uuid4 as uuid
from contextlib import contextmanager
from collections import namedtuple

from .BasePubSub import BasePublisher, BaseSubscriber, AlreadyExists, NotFound, DeadlineExceeded, do_test_publisher, do_test_subscriber

def test_subscriber():
    do_test_subscriber(GoogleSubscriber, GooglePublisher)

def test_publisher():
    do_test_publisher(GooglePublisher)
    
class GooglePublisher(BasePublisher):

    @classmethod
    def get_credentials(cls):
        credentials_path = os.environ['GOOGLE_CREDENTIALS']
        assert os.path.exists(credentials_path)
        log.debug(f"pubsub credentials path={credentials_path}")
        return google.oauth2.service_account.Credentials.from_service_account_file(credentials_path)

    @classmethod
    def get_publisher(cls):
        return pubsub_v1.PublisherClient(credentials=cls.get_credentials())

    @classmethod
    def topic_exists(cls, path):
        publisher = cls.get_publisher()
        try:
            publisher.get_topic(path)
        except google.api_core.exceptions.NotFound:
            return False
        else:
            return True
    
    def __init__(self, topic_name, private_topic=False, **kwargs):
        super(GooglePublisher, self).__init__(topic_name, private_topic=private_topic, **kwargs)

    def create_publisher(self ):
        return GooglePublisher.get_publisher()

    def compose_path(self, project, name):
        return self.publisher.topic_path(project, name)
        
    def create_topic(self, topic, **kwargs):
        try:
            self.publisher.create_topic(topic, **kwargs)
        except google.api_core.exceptions.AlreadyExists:
            raise AlreadyExists()
        
    def do_publish(self, path, message, **kwargs):
        self.publisher.publish(path,
                               message,
                               **kwargs)
    def do_delete_topic(self, path):
        self.publisher.delete_topic(path)
        
        
            
class GoogleSubscriber(BaseSubscriber):
    @classmethod
    def get_credentials(cls):
        credentials_path = os.environ['GOOGLE_CREDENTIALS']
        assert os.path.exists(credentials_path)
        log.debug(f"pubsub credentials path={credentials_path}")
        return google.oauth2.service_account.Credentials.from_service_account_file(credentials_path)

    @classmethod
    def get_subscriber(cls):
        return pubsub_v1.SubscriberClient(credentials=cls.get_credentials())

    @classmethod
    def subscription_exists(cls, path):
        subscriber = cls.get_subscriber()
        try:
            subscriber.get_subscription(path)
        except google.api_core.exceptions.NotFound:
            return False
        else:
            return True

    def __init__(self, subscription_name, topic, private_subscription=False, **kwargs):
        super(GoogleSubscriber, self).__init__(subscription_name, topic, private_subscription=private_subscription, **kwargs)
        
    def create_subscriber(self):
        self.credentials = get_credentials()
        return pubsub_v1.SubscriberClient(credentials=self.credentials)

    def compose_subscription_path(self, project, name):
        return self.subscriber.subscription_path(project, name)
    def compose_topic_path(self, project, name):
        return self.subscriber.topic_path(project, name)

    def get_subscription(self, path):
        try:
            return self.subscriber.get_subscription(path)
        except google.api_core.exceptions.NotFound:
            raise NotFound

    def create_subscription(self, sub_path, topic_path, **kwargs):
        return self.subscriber.create_subscription(sub_path, topic_path, **kwargs)

    
    PulledMessage = namedtuple("PulledMessage",  "data ack_id")
    def do_pull(self, path, max_messages=1, **kwargs):
        try:
            resp = self.subscriber.pull(path, max_messages, **kwargs)
            t = [GoogleSubscriber.PulledMessage(r.message.data, r.ack_id) for r in resp.received_messages]
            return t
        except google.api_core.exceptions.DeadlineExceeded:
            raise DeadlineExceeded

    def do_acknowledge(self, path, msg):
        self.subscriber.acknowledge(path, [msg.ack_id])

    def do_delete_subscription(self, path):
        self.subscriber.delete_subscription(path)

def get_publisher():
    return pubsub_v1.PublisherClient(credentials=get_credentials())

def get_subscriber():
    return pubsub_v1.SubscriberClient(credentials=get_credentials())
    
def get_credentials():
    credentials_path = os.environ['GOOGLE_CREDENTIALS']
    assert os.path.exists(credentials_path)
    log.debug(f"pubsub credentials path={credentials_path}")
    return google.oauth2.service_account.Credentials.from_service_account_file(credentials_path)

def compute_topic_path(topic):
    publisher = get_publisher()
    project = os.environ['GOOGLE_CLOUD_PROJECT']
    return  publisher.topic_path(project, topic)
def get_publisher():
    return pubsub_v1.PublisherClient(credentials=get_credentials())
    
def does_topic_exist(topic):
    publisher = get_publisher()
    try:
        publisher.get_topic(compute_topic_path(topic))
        return True
    except google.api_core.exceptions.NotFound:
        return False

def does_subscription_exist(subscription):
    subscriber = get_subscriber()
    try:
        subscriber.get_subscription(compute_subscription_path(subscription))
        return True
    except google.api_core.exceptions.NotFound:
        return False
        
def ensure_topic(topic):
    publisher = get_publisher()
    log.debug(f"Ensuring topic '{compute_topic_path(topic)}' exists")
    try:
        topic = publisher.create_topic(compute_topic_path(topic))
    except google.api_core.exceptions.AlreadyExists:
        log.debug(f"Topic '{compute_topic_path(topic)}' already exists")
        pass

def delete_topic(topic):
    publisher = get_publisher()
    publisher.delete_topic(compute_topic_path(topic))

def compute_subscription_path(subscription):
    subscriber = get_subscriber()
    return subscriber.subscription_path(os.environ['GOOGLE_CLOUD_PROJECT'], subscription)
    
def ensure_subscription_exists(topic, subscription, **kwargs):
    subscriber = get_subscriber()
    log.debug(f"Ensuring Subscription '{compute_subscription_path(subscription)}' exists")
    try:
        subscriber.create_subscription(compute_subscription_path(subscription),
                                       compute_topic_path(topic))#**kwargs)
    except google.api_core.exceptions.AlreadyExists:
        log.debug(f"Subscription '{compute_subscription_path(subscription)}' already exists")
        pass

def delete_subscription(subscription):
    subscriber = get_subscriber()
    subscriber.delete_subscription(compute_subscription_path(subscription))
    
def test_pubsub():
    import threading
    topic = f"test-{uuid()}"
    assert not does_topic_exist(topic)
    ensure_topic(topic)
    assert does_topic_exist(topic)
    # this shouldn't throw
    ensure_topic(topic)
    publisher = get_publisher()

    sub_name = f"sub-{topic}"
    ensure_subscription_exists(topic, sub_name)
    assert does_subscription_exist(sub_name)
    # shouldn't throw
    ensure_subscription_exists(topic, sub_name)

    subscriber = get_subscriber()
    def publish():
        log.debug(f"topic_path = {compute_topic_path(topic)}")
        publisher.publish(compute_topic_path(topic), "hello".encode("utf8"))

    threading.Timer(1, publish).start()

    log.debug(f"subscription_path = {compute_subscription_path('test')}")
    response = subscriber.pull(compute_subscription_path(sub_name), max_messages=1, timeout=10)
    assert response.received_messages[0].message.data.decode("utf8") == "hello"
    subscriber.acknowledge(compute_subscription_path(sub_name), [response.received_messages[0].ack_id])
    delete_subscription(sub_name)
    assert not does_subscription_exist(topic)
    delete_topic(topic)
    assert not does_topic_exist(topic)


class GooglePubSub(object):
    def __init__(self, subscription_name=None, private_subscription=False, subscription_base=None, **kwargs):

        if subscription_name:
            self.subscription_name = subscription_name
        else:
            if subscription_base is None:
                self.subscription_base =  os.environ['PUBSUB_SUBSCRIPTION']
            else:
                self.subscription_base = subscription_base

            if private_subscription:
                self.subscription_name = fr"{self.subscription_base}-{str(uuid())}"
            else:
                self.subscription_name = self.subscription_base
                
        self.topic = os.environ['PUBSUB_TOPIC']

        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        
        
        self.credentials = get_credentials()
        self.subscriber = pubsub_v1.SubscriberClient(credentials=self.credentials)
        self.subscription_path = self.subscriber.subscription_path(self.project, self.subscription_name)
        self.publisher = pubsub_v1.PublisherClient(credentials=self.credentials)
        self.topic_name = self.publisher.topic_path(self.project, self.topic)

        if private_subscription:
            self.subscription = self.subscriber.create_subscription(self.subscription_path, self.topic_name, **kwargs)

#        log.debug(f"env credentials path={os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
        log.debug(f"pubsub topic_name ={self.topic_name}")
        log.debug(f"pubsub subscription name={self.subscription_path}")

        
    def pull(self, max_messages=1, **kwargs):

        try:
            response = self.subscriber.pull(self.subscription_path, max_messages, **kwargs)
        except google.api_core.exceptions.DeadlineExceeded:
            return []

        if len(response.received_messages) > 0:
            for msg in response.received_messages:
                payload = msg.message.data.decode("utf8")
                log.debug(f"Received {payload}")
                self.subscriber.acknowledge(self.subscription_path, [msg.ack_id])
            return [msg.message.data.decode("utf8") for msg in response.received_messages]
        else:
            return []
        
    def push(self, job_id):

        log.debug(f"Publishing to {self.topic_name}")
        t = self.publisher.publish(
            self.topic_name,
            job_id.encode("utf8")
        )
        log.debug(f"Result = {t.result()}")


    def tear_down(self):
        self.subscriber.delete_subscription(self.subscription_path)
        
def _test_push():

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
