import os
import logging as log
from pathlib import Path
import pytest
import tempfile


class LocalPubSub(object):
    def __init__(self, directory=None):
        if directory == None:
            if "EMULATION_DIR" in os.environ:
                log.debug("creating existing directory")
                directory = os.environ["EMULATION_DIR"]
            else:
                log.debug("creating new directory")
                self.tmp_dir = tempfile.TemporaryDirectory()
                directory = self.tmp_dir.name

        log.debug(f"Using directory {directory}")
        self.directory = directory
        assert os.path.isdir(directory)
        
        self.inbox = os.path.join(os.path.join(self.directory, "inbox"))
        self.outbox = os.path.join(os.path.join(self.directory, "outbox"))
                               
        if not os.path.exists(self.inbox):
            log.debug(f"Creating inbox: {self.inbox}")
            os.mkdir(self.inbox)
            
        if not os.path.exists(self.outbox):
            log.debug(f"Creating outbox: {self.outbox}")
            os.mkdir(self.outbox)
                      
    def load_inbox(self):
        p = Path(self.inbox)
        return list(sorted(p.glob('*')))

    def pull(self):
        paths = self.load_inbox()
        if not paths:
            return None
        
        path = os.path.join(self.inbox, paths[0])
        log.debug(f"Loading pull from {path}")
        with open(path, "r") as f:
            r = f.read()
            log.debug(f"Data: {r}")
        log.debug(f"Deleting {path}")
        os.unlink(path)
        return r

    def push(self, job_id):
        paths = self.load_inbox()
        if not paths:
            last = 0
        else:
            last = int(str(self.load_inbox()[-1].parts[-1]))
        path = os.path.join(self.inbox, f"{last + 1}")
        log.debug(f"Writing {job_id} to {path}")
        with open(path, "w") as f:
            f.write(job_id)

def do_test(pubsub):
    to_send = set(map(str, [1 , 2, 3 ,4]))

    for i in to_send:
        pubsub.push(i)

    while len(to_send):
        r = pubsub.pull()
        to_send -= {r}
        
def test_pub_sub():
    try:
        del os.environ['EMULATION_DIR']
    except:
        pass
    from .CloudServices import PubSub
    assert PubSub == LocalPubSub

    do_test(PubSub())
    
    with tempfile.TemporaryDirectory(prefix="ENVIRON") as td:
        log.debug(f"Created temp directory: {td}")
        os.environ["EMULATION_DIR"] = td
        t = PubSub()
        do_test(t)


    
