import os

if os.environ["DEPLOYMENT_MODE"] == "EMULATION":
    from .LocalPubSub import LocalPublisher as Publisher
    from .LocalPubSub import LocalSubscriber as Subscriber
else:
    from .GooglePubSub import GooglePublisher as Publisher
    from .GooglePubSub import GoogleSubscriber as Subscriber
