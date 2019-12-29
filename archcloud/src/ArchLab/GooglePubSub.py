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
    def get_publisher(cls):
        return pubsub_v1.PublisherClient()

    @classmethod
    def topic_exists(cls, path):
        publisher = cls.get_publisher()
        try:
            publisher.get_topic(path)
        except google.api_core.exceptions.NotFound:
            return False
        else:
            return True
    
    def __init__(self, topic, private_topic=False, **kwargs):
        super(GooglePublisher, self).__init__(topic, private_topic=private_topic, **kwargs)

    def create_publisher(self ):
        return GooglePublisher.get_publisher()

    def compose_path(self, project, name):
        return self.publisher.topic_path(project, name)
        
    def create_topic(self, topic, **kwargs):
        try:
            self.publisher.create_topic(topic, **kwargs)
        except google.api_core.exceptions.AlreadyExists as e:
            raise AlreadyExists(repr(e))
        
    def do_publish(self, path, message, **kwargs):
        self.publisher.publish(path,
                               message,
                               **kwargs)
    def do_delete_topic(self, path):
        self.publisher.delete_topic(path)
        
        
            
class GoogleSubscriber(BaseSubscriber):

    @classmethod
    def get_subscriber(cls):
        return pubsub_v1.SubscriberClient()

    @classmethod
    def subscription_exists(cls, path):
        subscriber = cls.get_subscriber()
        try:
            subscriber.get_subscription(path)
        except google.api_core.exceptions.NotFound:
            return False
        else:
            return True

    def __init__(self, topic, name=None, **kwargs):
        super(GoogleSubscriber, self).__init__(topic, name=name, **kwargs)

    def create_subscriber(self):
        return pubsub_v1.SubscriberClient()

    def compose_subscription_path(self, project, name):
        return self.subscriber.subscription_path(project, name)

    def compose_topic_path(self, project, name):
        return self.subscriber.topic_path(project, name)

    def get_subscription(self, path):
        try:
            return self.subscriber.get_subscription(path)
        except google.api_core.exceptions.NotFound as e:
            raise NotFound(e)

    def create_subscription(self, sub_path, topic_path, **kwargs):

        try:
            GooglePublisher.get_publisher().create_topic(topic_path)
        except google.api_core.exceptions.AlreadyExists:
            pass

        try:
            return self.subscriber.create_subscription(sub_path, topic_path, **kwargs)
        except google.api_core.exceptions.AlreadyExists as e: 
            raise AlreadyExists(repr(e))
            

    
    PulledMessage = namedtuple("PulledMessage",  "data ack_id")
    def do_pull(self, path, max_messages=1, **kwargs):
        try:
            resp = self.subscriber.pull(path, max_messages, **kwargs)
            t = [GoogleSubscriber.PulledMessage(r.message.data, r.ack_id) for r in resp.received_messages]
            return t
        except google.api_core.exceptions.DeadlineExceeded:
            raise DeadlineExceeded

    def do_acknowledge(self, path, msg):
        try:
            self.subscriber.acknowledge(path, [msg.ack_id])
        except:
            pass

    def do_delete_subscription(self, path):
        self.subscriber.delete_subscription(path)
