import tempfile
import stat
from pathlib import Path
import pytest
from ksei import (
    KSEIClient,
    FileAuthStore,
    get_expire_time,
    mask_secret,
    KSEIError,
    KSEIAuthError,
)


def test_auth_store_permissions_and_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileAuthStore(directory=tmpdir)
        
        # Test directory permissions (0o700)
        dir_stat = Path(tmpdir).stat().st_mode
        assert bool(dir_stat & stat.S_IRUSR)
        assert bool(dir_stat & stat.S_IWUSR)
        assert bool(dir_stat & stat.S_IXUSR)

        assert store.get("test_user") is None

        # Test set and file permissions (0o600)
        assert store.set("test_user", {"token": "sample_token_123"}) is True
        token_file = Path(tmpdir) / "test_user.json"
        assert token_file.exists()
        file_stat = token_file.stat().st_mode & 0o777
        assert file_stat == 0o600

        # Test get
        cached = store.get("test_user")
        assert cached == {"token": "sample_token_123"}

        # Test delete
        assert store.delete("test_user") is True
        assert store.get("test_user") is None


def test_secret_masking():
    assert mask_secret(None) == "<empty>"
    assert mask_secret("") == "<empty>"
    assert mask_secret("short") == "*****"
    assert mask_secret("supersecretpassword") == "su***************rd"


def test_client_init():
    client = KSEIClient(username="myuser", password="mypassword")
    assert client.username == "myuser"
    assert client.base_url == "https://akses.ksei.co.id/service"
    assert client.timeout == 30.0
    assert "mypassword" not in repr(client)  # Password should not appear in repr


def test_client_missing_credentials():
    client = KSEIClient(username="", password="")
    with pytest.raises(KSEIAuthError):
        client._login(client._get_sync_client())


def test_default_auth_store():
    # FileAuthStore() without arguments should default to user cache
    store = FileAuthStore()
    assert ".cache" in str(store.directory) or "ksei" in str(store.directory)

    # KSEIClient without auth_store should automatically instantiate FileAuthStore
    client = KSEIClient(username="test", password="pw")
    assert isinstance(client.auth_store, FileAuthStore)

    # Disabling cache with auth_store=False
    client_no_cache = KSEIClient(username="test", password="pw", auth_store=False)
    assert client_no_cache.auth_store is None


def test_get_expire_time_invalid():
    assert get_expire_time("invalid_token") is None


def test_client_custom_user_agent():
    custom_ua = "CustomUserAgent/1.0"
    client = KSEIClient(username="test", password="pw", user_agent=custom_ua)
    assert client.user_agent == custom_ua

    # Default user agent should be a non-empty string
    client_default = KSEIClient(username="test", password="pw")
    assert bool(client_default.user_agent)

