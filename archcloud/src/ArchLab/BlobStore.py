import os
import logging as log

if os.environ["CLOUD_MODE"] == "EMULATION":
    log.debug("Using emulated blob store")
    from .LocalBlobStore import LocalBlobStore as BlobStore
else:
    log.debug("Using google blob store")
    from .GoogleBlobStore import GoogleBlobStore as BlobStore
