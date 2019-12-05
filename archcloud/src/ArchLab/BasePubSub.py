import os
import logging as log
from uuid import uuid4 as uuid

class AlreadyExists(Exception):
    pass
class NotFound(Exception):
    pass
class DeadlineExceeded(Exception):
    pass

class PubSubAgent(object):

    def add_namespace(self, name):
        return f'{os.environ["GOOGLE_RESOURCE_PREFIX"]}-{name}'

class BasePublisher(PubSubAgent):
    def __init__(self, topic_name, private_topic=False, **kwargs):
        log.debug("BasePublisher Constructor")        
        
        if private_topic:
            self.topic_name = f"{topic_name}-{str(uuid())}"
        else:
            self.topic_name = topic_name

        self._topic_name = self.add_namespace(self.topic_name)
            
        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        self.private_topic = private_topic
        
        self.publisher = self.create_publisher()
        self.topic_path = self.compose_path(self.project, self._topic_name)

        try:
            log.debug(f"Trying to create topic {self.topic_path}")
            self.topic = self.create_topic(self.topic_path, **kwargs)
        except AlreadyExists:
            log.debug(f"Topic '{self.topic_path}' already exists")
            if private_topic:
                raise
        else:
            log.debug(f"Created pubsub topic '{self.topic_path}'")

    def publish(self, message,**kwargs):
        log.debug(f"Publishing to {self._topic_name}: {message}")
        return self.do_publish(self.topic_path,
                               message.encode("utf8"),
                               **kwargs)


    def delete_topic(self, force=False):
        if self.private_topic or force:
            log.info(f"Deleting topic {self.topic_path}")
            self.do_delete_topic(self.topic_path)
        else:
            log.debug(f"Not deleting topic {self.topic_path}, since no force")
            
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        self.delete_topic()
            

class BaseSubscriber(PubSubAgent):

    def __init__(self, subscription_name, topic, private_subscription=False, **kwargs):

        if private_subscription:
            self.subscription_name = f"{subscription_name}-{str(uuid())}"
        else:
            self.subscription_name = subscription_name

        self._subscription_name = self.add_namespace(self.subscription_name)
        self.private_subscription = private_subscription
        
        self.topic_name = topic
        self._topic_name = self.add_namespace(topic)

        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        self.subscriber = self.create_subscriber()

        self.subscription_path = self.compose_subscription_path(self.project, self._subscription_name)
        self.topic_path = self.compose_topic_path(self.project, self._topic_name)

        if private_subscription or not type(self).subscription_exists(self.subscription_path):
            log.debug(f"Creating subscription: {self.subscription_path}")
            self.subscription = self.create_subscription(self.subscription_path, self.topic_path, **kwargs)
        
    def pull(self, max_messages=1, **kwargs):
        log.debug(f"Pulling on {self.subscription_path}")
        try:
            messages = self.do_pull(self.subscription_path, max_messages, **kwargs)
        except DeadlineExceeded:
            log.debug(f"Pulling on {self.subscription_path} timedout")
            return []

        if len(messages) > 0:
            log.debug(f"Pulling on {self.subscription_path} provided {len(messages)} messages")
            r = []
            for msg in messages:
                payload = msg.data.decode("utf8")
                r.append(payload)
                log.debug(f"Received {payload}")
                log.debug(f"Acking message {payload}")
                self.do_acknowledge(self.subscription_path, msg)
            return r
        else:
            return []

    def delete_subscription(self, force=False):

        if self.private_subscription or force:
            log.info(f"Deleting subscription {self.subscription_path}")
            self.do_delete_subscription(self.subscription_path)
        else:
            log.debug(f"Not deleting subscripti {self.subscription_path}, since no force")

    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        self.delete_subscription()
    
def do_test_publisher(PublisherType):
    id = str(uuid())
    t = PublisherType(f"test-topic-{id}")
    t.publish("hello")
    t.publish("bye", fore="now")

    assert PublisherType.topic_exists(t.topic_path)
    t.delete_topic(force=True)
    assert not PublisherType.topic_exists(t.topic_path)

    with PublisherType(f"test-topic-{id}", private_topic=True) as t2:
        t2.publish("hello")
        assert t2.topic_path != t.topic_path

        t2_path = t2.topic_path
        assert PublisherType.topic_exists(t2.topic_path)

    assert not PublisherType.topic_exists(t2_path)

    t3 = PublisherType(f"test3-topic-{id}")
    with PublisherType(f"test3-topic-{id}", private_topic=False) as t4:
        t4.publish("hello")
        assert t3.topic_path == t4.topic_path

    assert PublisherType.topic_exists(t3.topic_path)

    t3.delete_topic()
    assert PublisherType.topic_exists(t3.topic_path) 

    t3.delete_topic(force=True)
    assert not PublisherType.topic_exists(t3.topic_path)

def do_test_subscriber(SubscriberType, PublisherType):
    import copy
    
    id = str(uuid())
    with PublisherType(f"sub-test-topic-{id}", private_topic=True) as topic:
        s = SubscriberType(f"sub-test-sub-{id}", topic=topic.topic_name)
        assert SubscriberType.subscription_exists(s.subscription_path)
        topic.publish("Hello")
        assert s.pull(timeout=4)[0] == "Hello"
        s.delete_subscription(force=True)
        assert not SubscriberType.subscription_exists(s.subscription_path)

        items = set(map(str, range(0,3)))

        shared1 = SubscriberType(f"sub2-test-sub-{id}", topic=topic.topic_name)
        shared2 = SubscriberType(f"sub2-test-sub-{id}", topic=topic.topic_name)
        private = SubscriberType(f"sub2-test-sub-{id}", topic=topic.topic_name, private_subscription=True)
        
        for i in items:
            topic.publish(str(i))

        missing = copy.deepcopy(items)
        for i in range(0,20):
            log.debug('shared 1')
            for m in shared1.pull(timeout=1, max_messages=1):
                log.debug(f"shared 1 Got {m}")
                assert m in missing
                missing.remove(m)
            log.debug('shared 2')
            for m in shared2.pull(timeout=1, max_messages=1):
                log.debug(f"shared 2 Got {m}")
                assert m in missing
                missing.remove(m)
            if not missing:
                break
        assert len(missing) == 0

        missing2 = copy.deepcopy(items)
        for i in range(0,100):
            log.debug('private')
            for m in private.pull(timeout=1, max_messages=1):
                missing2.remove(m)
            if not missing2:
                break
        assert len(missing2) == 0

        with SubscriberType(f"sub3-test-sub-{id}", private_subscription=True, topic=topic.topic_name) as s5:
            assert SubscriberType.subscription_exists(s5.subscription_path)
            s5_path = s5.subscription_path

        assert not SubscriberType.subscription_exists(s5_path)
            
        with SubscriberType(f"sub3-test-sub-{id}", private_subscription=False,topic=topic.topic_name) as s6:
            assert SubscriberType.subscription_exists(s6.subscription_path)
            s6_path = s6.subscription_path

        assert SubscriberType.subscription_exists(s6_path)
        SubscriberType.delete_subscription(s6_path)
