import pytest

class NotFound(Exception):
    pass

class BaseBlobStore(object):
    pass


def do_test_blob_store(BlobStoreType):
    import pytest
    bs = BlobStoreType("testing-bucket-remove-at-will")
    bs.write_file("test", "hello")
    assert "hello" == bs.read_file("test")

    with pytest.raises(NotFound):
        bs.read_file("fail")
