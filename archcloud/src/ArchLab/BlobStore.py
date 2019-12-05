import os

if os.environ["DEPLOYMENT_MODE"] == "EMULATION":
    from .LocalBlobStore import LocalBlobStore as BlobStore
else:
    from .GooglePubSub import GoogleBlobStore as BlobStore
