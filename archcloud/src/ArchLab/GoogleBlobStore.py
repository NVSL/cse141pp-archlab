from google.cloud import storage
import google.cloud
import os
from .BaseBlobStore import BaseBlobStore, do_test_blob_store, NotFound
    
class GoogleBlobStore(object):
    def __init__(self, bucket):
        self.project = os.environ['GOOGLE_CLOUD_PROJECT']
        self.client = storage.client.Client(self.project)
        self.bucket_name = f"{os.environ['GOOGLE_RESOURCE_PREFIX']}-{bucket}".lower()
        try:
            self.bucket = self.client.get_bucket(self.bucket_name)
        except google.cloud.exceptions.NotFound:
            self.bucket = self.client.create_bucket(self.bucket_name)


    def write_file(self, filename, contents, owner=None):
        blob = self.bucket.blob(filename)
        acl = blob.acl
        blob.upload_from_string(contents.encode('utf8'))
        acl.user(owner).grant_read()
        acl.save()
        return self.get_url(filename)
    
    def read_file(self, filename):
        blob = self.bucket.get_blob(filename)
        if not blob:
            raise NotFound
        return blob.download_as_string().decode("utf8")

    def get_url(self, filename):
        return f"https://storage.cloud.google.com/{self.bucket_name}/{filename}"

                 
def test_google_blob_store():
    do_test_blob_store(GoogleBlobStore)
