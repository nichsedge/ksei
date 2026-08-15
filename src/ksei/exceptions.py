"""
Custom exception classes for KSEI client and server.
"""


class KSEIError(Exception):
    """Base exception for all KSEI errors."""

    pass


class KSEIAuthError(KSEIError):
    """Raised when authentication fails or credentials/tokens are invalid."""

    pass


class KSEINetworkError(KSEIError):
    """Raised when a network or HTTP communication error occurs."""

    pass


class KSEIResponseError(KSEIError):
    """Raised when the API returns an error response or unexpected structure."""

    pass
