import os

if os.environ["DEPLOYMENT_MODE"] == "EMULATION":
    from .LocalDataStore import LocalDataStore as DS
    from .LocalPubSub import LocalPubSub as PubSub
else:
    from .GoogleDataStore import GoogleDataStore as DS
    from .GooglePubSub import GooglePubSub as PubSub

