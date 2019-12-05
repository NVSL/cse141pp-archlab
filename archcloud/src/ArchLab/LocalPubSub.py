import os
import logging as log
from pathlib import Path
import pytest
import tempfile
import time
from uuid import uuid4 as uuid
from collections import namedtuple
import shutil

from .BasePubSub import BasePublisher, BaseSubscriber, AlreadyExists, NotFound, DeadlineExceeded, do_test_publisher, do_test_subscriber

def test_subscriber():
    do_test_subscriber(LocalSubscriber, LocalPublisher)

def test_publisher():
    do_test_publisher(LocalPublisher)

class LocalPubSubAgent(object):

    def __init__(self, *argc, **kwargs):
        log.debug("LocalPubSubAgent Constructor")
        self.topics_root = LocalPubSubAgent.get_topics_root()
        os.makedirs(self.topics_root, exist_ok=True)
        self.subscriptions_root = LocalPubSubAgent.get_subscriptions_root()
        os.makedirs(self.subscriptions_root, exist_ok=True)

    @classmethod
    def get_topics_root(cls):
        return os.path.join(os.environ['EMULATION_DIR'], os.environ['GOOGLE_CLOUD_PROJECT'], "pubsub", "topics")
    @classmethod
    def get_subscriptions_root(cls):
        return os.path.join(os.environ['EMULATION_DIR'], os.environ['GOOGLE_CLOUD_PROJECT'], "pubsub", "subscriptions")
        
    def compose_subscription_path(self, project, name):
        return f"{project}-{name}"
    
    def compose_topic_path(self, project, name):
        return f"{project}-{name}"

    def compose_path(self, project, name):
        return f"{project}-{name}"
    
class LocalPublisher(LocalPubSubAgent, BasePublisher):

    def __init__(self, topic, private_topic=False, **kwargs):
        LocalPubSubAgent.__init__(self)
        BasePublisher.__init__(self, topic, private_topic=private_topic, **kwargs)
         
    @classmethod
    def topic_exists(cls, path):
        return os.path.isdir(os.path.join(LocalPubSubAgent.get_topics_root(), path))
    
    def create_publisher(self):
        return None

    def create_topic(self, topic, **kwargs):
        try:
            log.debug(f"Making {os.path.join(self.topics_root, topic)}")
            return os.mkdir(os.path.join(self.topics_root, topic))
        except OSError:
            raise AlreadyExists()
        
    def do_publish(self, path, message, **kwargs):
        fn = str(uuid())
        log.debug(f"Publishing to topic {self.topic_path}")
        for subscription in os.listdir(self.subscriptions_root):
            subscription = os.path.join(self.subscriptions_root, subscription)
            log.debug(f"Found subscription {subscription}")
            if os.path.isdir(subscription):
                with open(os.path.join(subscription, "topic")) as out:
                    topic = out.read()
                    log.debug(f"It is for topic '{repr(topic)}'")
                    if topic== self.topic_path:
                        log.debug(f"It is a match.  Writing to {fn}")
                        with open(os.path.join(subscription, fn), "wb") as out:
                            out.write(message)
                    else:
                        log.debug(f"It is not a match for '{repr(self.topic_path)}'")
                                        
    def do_delete_topic(self, path):
        shutil.rmtree(os.path.join(self.topics_root, path))
        
class LocalSubscriber(LocalPubSubAgent, BaseSubscriber):
    def __init__(self, topic, name=None, **kwargs):
        LocalPubSubAgent.__init__(self)
        BaseSubscriber.__init__(self, topic=topic, name=name, **kwargs)
    
    @classmethod
    def subscription_exists(cls, sub_path):
        return os.path.isdir(os.path.join(LocalPubSubAgent.get_subscriptions_root(), sub_path))
        
    def create_subscriber(self):
        return None

    def create_subscription(self, sub_path, topic_path, **kwargs):
        p = os.path.join(self.subscriptions_root, sub_path)
        log.debug(f"looking for {p}")
        if not os.path.isdir(p):
            os.mkdir(p)
            log.debug(f"Creating subscription {sub_path}")
            with open(os.path.join(p, "topic"), "w") as f:
                f.write(topic_path)
        else:
            raise AlreadyExists
    
    PulledMessage = namedtuple("PulledMessage",  "data ack_id")
    def do_pull(self, path, max_messages=1, **kwargs):
        sub = os.path.join(self.subscriptions_root, path)
        items = list(filter(lambda x: x != "topic", os.listdir(sub)))
        log.debug(f"Directory contents for {path} {list(items)} ")
        c = 0
        r = []
        for i in items:
            t = f"tmp_{uuid()}"
            try:
                log.debug(f"Grabbing {i} moving to {t}")
                os.rename(os.path.join(sub, i),
                          os.path.join(sub, t)) # atomically remove it
                assert not os.path.exists(os.path.join(sub, i))
            except:
                log.debug(f"Missed!")
                continue # someone else might have got to it first.
            log.debug(f"Got it! reading {t}")
            with open(os.path.join(sub, t), "rb") as f:
                r.append(LocalSubscriber.PulledMessage(f.read(), None))
            log.debug(f"Removing {t}")
            os.remove(os.path.join(sub, t))
            c += 1
            if c == max_messages:
                break
        return r

    def do_acknowledge(self, path, msg):
        pass

    def do_delete_subscription(self, path):
        shutil.rmtree(os.path.join(self.subscriptions_root, path))
