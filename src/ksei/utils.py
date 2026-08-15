import json
import os
import re
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def mask_secret(secret: Optional[str], show_chars: int = 2) -> str:
    """
    Mask a sensitive string for safe logging/display.
    E.g. 'mypassword123' -> 'my*********23'
    """
    if not secret:
        return "<empty>"
    if len(secret) <= (show_chars * 2 + 1):
        return "*" * len(secret)
    return f"{secret[:show_chars]}{'*' * (len(secret) - show_chars * 2)}{secret[-show_chars:]}"


def _sanitize_key(key: str) -> str:
    """Sanitize key to prevent path traversal or filesystem issues."""
    sanitized = re.sub(r"[^a-zA-Z0-9_.-]", "_", key)
    return sanitized or "default"


class FileAuthStore:
    """
    Secure file-based storage for authentication tokens.
    Enforces restricted filesystem permissions (0o700 for directories, 0o600 for files).
    """

    def __init__(self, directory: str = "./data"):
        self.directory = Path(directory).resolve()
        # Create directory with owner-only access (0o700)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Ensure permissions in case directory already existed
        try:
            self.directory.chmod(0o700)
        except OSError:
            pass
        logger.debug(f"Initialized FileAuthStore in {self.directory}")

    def _get_path(self, key: str) -> Path:
        safe_key = _sanitize_key(key)
        return self.directory / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the store by key.
        """
        path = self._get_path(key)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read auth cache for {mask_secret(key)}: {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        Store a value securely with owner-only (0o600) permissions.
        """
        path = self._get_path(key)
        try:
            # Open file with descriptor specifying 0o600 permissions
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
            mode = 0o600
            fd = os.open(path, flags, mode)
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
            return True
        except (OSError, TypeError) as e:
            logger.error(f"Failed to save auth cache for {mask_secret(key)}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Remove cached value for key.
        """
        path = self._get_path(key)
        try:
            if path.exists():
                path.unlink()
            return True
        except OSError as e:
            logger.warning(f"Failed to delete auth cache for {mask_secret(key)}: {e}")
            return False

    def __repr__(self) -> str:
        return f"FileAuthStore(directory={self.directory})"
