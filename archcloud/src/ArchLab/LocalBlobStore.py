import os
from .GoogleBlobStore import NotFound


class LocalBlobStore(object):
    def __init__(self, bucket):
        self.emulation_dir = os.environ['EMULATION_DIR']
        self.directory = os.path.join(self.emulation_dir, bucket)
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def write_file(self, filename, contents):
        with open(os.path.join(self.directory, filename), "w") as f:
            f.write(contents)

    def read_file(self, filename):
        try:
            with open(os.path.join(self.directory, filename)) as f:
                return f.read()
        except FileNotFoundError:
            raise NotFound

def test_local_blob_store():
    from .GoogleBlobStore import _test_blob_store
    if "EMULATION_DIR" not in os.environ:
        return
    bs = LocalBlobStore("test-bucket")
    _test_blob_store(bs)
