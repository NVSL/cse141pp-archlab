import pytest

class NotFound(Exception):
    pass

class BaseBlobStore(object):
    pass


def do_test_blob_store(BlobStoreType):
    import pytest
    bs = BlobStoreType("Testing-Bucket-remove-at-will")
    url = bs.write_file("test-2", "hello", "steven.swanson@gmail.com")
    assert "file://" in url or "http" in url
    assert "hello" == bs.read_file("test-2")
    
    with pytest.raises(NotFound):
        bs.read_file("fail")
