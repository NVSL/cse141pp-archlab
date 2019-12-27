import os
from .BaseBlobStore import NotFound, BaseBlobStore, do_test_blob_store
import pytest

class LocalBlobStore(BaseBlobStore):
    def __init__(self, bucket):
        self.directory = os.path.join(os.environ["EMULATION_DIR"],
                                      os.environ['GOOGLE_CLOUD_PROJECT'],
                                      "blobstore",
                                      bucket)
        os.makedirs(self.directory, exist_ok=True)

    def write_file(self, filename, contents, content_disposition=None, content_type=None, owner=None):
        try:
            with open(os.path.join(self.directory, filename), "w") as f:
                f.write(contents)
        except TypeError:
            with open(os.path.join(self.directory, filename), "wb") as f:
                f.write(contents)
        return self.get_url(filename)
    
    def read_file(self, filename):
        try:
            with open(os.path.join(self.directory, filename)) as f:
                return f.read()
        except FileNotFoundError:
            raise NotFound
    def get_url(self, filename):
        return f"file://{os.path.abspath(os.path.join(self.directory, filename))}"
    
def test_local_blob_store():
    if "EMULATION_DIR" not in os.environ:
        pytest.skip()
    do_test_blob_store(LocalBlobStore)
