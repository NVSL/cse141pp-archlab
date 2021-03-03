import os
import logging as log

if os.environ["CLOUD_MODE"] == "EMULATION":
    log.debug("Using emulated pubsub")
    from .LocalPubSub import LocalPublisher as Publisher
    from .LocalPubSub import LocalSubscriber as Subscriber
else:
    log.debug("Using google pubsub")
    from .GooglePubSub import GooglePublisher as Publisher
    from .GooglePubSub import GoogleSubscriber as Subscriber
