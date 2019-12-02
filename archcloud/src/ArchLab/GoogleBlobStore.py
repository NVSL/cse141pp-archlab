from google.cloud import storage
import google.cloud
import os

class NotFound(Exception):
    pass

class GoogleBlobStore(object):
    def __init__(self, bucket):
        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        self.client = storage.client.Client(self.project)#, credentials=os.environ['GOOGLE_CREDENTIALS'])
        self.bucket_name = f"{os.environ['GOOGLE_RESOURCE_PREFIX']}-{bucket}"
        try:
            self.bucket = self.client.get_bucket(self.bucket_name)
        except google.cloud.exceptions.NotFound:
            self.bucket = self.client.create_bucket(self.bucket_name)


    def write_file(self, filename, contents):
        blob = self.bucket.blob(filename)
        blob.upload_from_string(contents.encode('utf8'))
        pass

    def read_file(self, filename):
        blob = self.bucket.get_blob(filename)
        if not blob:
            raise NotFound
        return blob.download_as_string().decode("utf8")


def _test_blob_store(bs):
    import pytest
    bs.write_file("test", "hello")
    assert "hello" == bs.read_file("test")

    with pytest.raises(NotFound):
        bs.read_file("fail")
                 
def test_google_blob_store():

    bs = GoogleBlobStore("test-bucket")
    _test_blob_store(bs)
