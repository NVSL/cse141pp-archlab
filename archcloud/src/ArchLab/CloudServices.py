import os
import logging as log

if os.environ["DEPLOYMENT_MODE"] == "EMULATION":
    from .LocalDataStore import LocalDataStore as DS
    from .LocalPubSub import LocalPubSub as PubSub
    from .LocalBlobStore import LocalBlobStore as BlobStore
else:
    from .GoogleDataStore import GoogleDataStore as DS
    from .GooglePubSub import GooglePubSub as PubSub
    from .GoogleBlobStore import GoogleBlobStore as BlobStore

def GetDS():
    if os.environ["DEPLOYMENT_MODE"] == "EMULATION":
        from .LocalDataStore import LocalDataStore as DS
    else:
        from .GoogleDataStore import GoogleDataStore as DS

    return DS

def GetPubSub():
    if os.environ["DEPLOYMENT_MODE"] == "EMULATION":
        from .LocalPubSub import LocalPubSub as PubSub
    else:
        from .GooglePubSub import GooglePubSub as PubSub

    return PubSub

def GetBlobStore():
    if os.environ["DEPLOYMENT_MODE"] == "EMULATION":
        from .LocalBlobStore import LocalBlobStore as BlobStore
    else:
        from .GoogleBlobStore import GoogleBlobStore as BlobStore

    return BlobStore
