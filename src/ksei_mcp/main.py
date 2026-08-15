"""
Legacy shim module for ksei_mcp.
Points to ksei.server for backwards compatibility.
"""

from ksei.server import run, main, server, get_ksei_client, KSEIClient, FileAuthStore

__all__ = ["run", "main", "server", "get_ksei_client", "KSEIClient", "FileAuthStore"]


if __name__ == "__main__":
    run()
