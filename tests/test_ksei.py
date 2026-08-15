import tempfile
import pytest
from ksei import KSEIClient, FileAuthStore, get_expire_time


def test_auth_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileAuthStore(directory=tmpdir)
        assert store.get("test_user") is None

        store.set("test_user", "sample_token")
        assert store.get("test_user") == "sample_token"


def test_client_init():
    client = KSEIClient(username="myuser", password="mypassword")
    assert client.username == "myuser"
    assert client.base_url == "https://akses.ksei.co.id/service"
    assert client.timeout == 30.0


def test_get_expire_time_invalid():
    assert get_expire_time("invalid_token") is None
