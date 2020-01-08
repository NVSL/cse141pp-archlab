import pytest

class NotFound(Exception):
    pass

class BaseBlobStore(object):
    pass


def do_test_blob_store(BlobStoreType):
    import pytest
    bs = BlobStoreType("Testing-Bucket-remove-at-will")
    url = bs.write_file("test-2", "hello", "steven.swanson@gmail.com")
    url = bs.write_file("test-1", "hello", "steven.swanson@gmail.com")
    
    assert "file://" in url or "http" in url
    assert "hello" == bs.read_file("test-2")
    assert len(bs.get_files_by_prefix("test")) == 2, "prefix match didn't work"
    
    with pytest.raises(NotFound):
        bs.read_file("fail")
