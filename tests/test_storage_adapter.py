from sicav_checker.storage.local_storage import LocalStorageAdapter


def test_local_storage_adapter_roundtrip(tmp_path) -> None:
    adapter = LocalStorageAdapter(tmp_path)
    adapter.save_bytes("folder/file.txt", b"hello")

    assert adapter.exists("folder/file.txt")
    assert adapter.load_bytes("folder/file.txt") == b"hello"