import os
import logging as log

if os.environ["CLOUD_MODE"] == "EMULATION":
    log.debug("Using emulated datastore")
    from .LocalDataStore import LocalDataStore as DataStore
else:
    log.debug("Using google datastore")
    from .GoogleDataStore import GoogleDataStore as DataStore
