from google.cloud import storage
import google.cloud
import os
from .BaseBlobStore import BaseBlobStore, do_test_blob_store, NotFound
    
class GoogleBlobStore(object):
    def __init__(self, bucket):
        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        self.client = storage.client.Client(self.project)
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


                 
def test_google_blob_store():
    do_test_blob_store(GoogleBlobStore)
