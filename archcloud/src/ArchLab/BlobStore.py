import os
import logging as log

if os.environ["CLOUD_MODE"] == "EMULATION":
    from .LocalBlobStore import LocalBlobStore as BlobStore
else:
    from .GoogleBlobStore import GoogleBlobStore as BlobStore
