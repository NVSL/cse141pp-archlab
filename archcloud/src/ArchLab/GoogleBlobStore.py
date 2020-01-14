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


    def write_file(self, filename, contents, content_disposition=None, content_type=None, owner=None):
        blob = self.bucket.blob(filename)
        if content_disposition:
            blob.content_disposition = content_disposition
        acl = blob.acl
        blob.upload_from_string(contents, content_type=content_type)
        if owner:
            acl.user(owner).grant_read()
            acl.save()
        return self.get_url(filename)
    
    def read_file(self, filename):
        blob = self.bucket.get_blob(filename)
        if not blob:
            raise NotFound
        try:
            return blob.download_as_string().decode("utf8")
        except UnicodeDecodeError:
            return blob.download_as_string()

    def get_url(self, filename):
        return f"https://storage.cloud.google.com/{self.bucket_name}/{filename}"

    def get_files_by_prefix(self, prefix):
        return [b.name for b in  self.client.list_blobs(self.bucket_name, prefix=prefix)]
        
                 
def test_google_blob_store():
    do_test_blob_store(GoogleBlobStore)
