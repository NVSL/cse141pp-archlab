import os
import logging as log

if os.environ["CLOUD_MODE"] == "EMULATION":
    from .LocalDataStore import LocalDataStore as DataStore
else:
    from .GoogleDataStore import GoogleDataStore as DataStore
