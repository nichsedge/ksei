import time
import hashlib
import base64
from urllib.parse import quote
import jwt
from fake_useragent import UserAgent
import asyncio
import threading
import httpx
from typing import Any, Dict, List, Optional, Union
import logging

from ksei.exceptions import KSEIAuthError, KSEINetworkError, KSEIResponseError
from ksei.utils import mask_secret

logger = logging.getLogger(__name__)


def get_expire_time(token: str) -> Optional[int]:
    """
    Get the expiration time from a JWT token.

    Args:
        token: The JWT token string

    Returns:
        The expiration timestamp as an integer or None if invalid
    """
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("exp")
    except (jwt.DecodeError, Exception) as e:
        logger.debug(f"Failed to decode JWT expiration: {e}")
        return None


class KSEIClient:
    """
    Client for interacting with PT Kustodian Sentral Efek Indonesia (AKSes KSEI) API.
    Supports both synchronous and asynchronous operations with connection reuse and token caching.
    """

    def __init__(
        self,
        username: str = "",
        password: str = "",
        auth_store=None,
        plain_password: bool = True,
        timeout: float = 30.0,
    ):
        self.base_url = "https://akses.ksei.co.id/service"
        self.base_referer = "https://akses.ksei.co.id"

        if auth_store is False:
            self.auth_store = None
        elif auth_store is None:
            from ksei.utils import FileAuthStore
            self.auth_store = FileAuthStore()
        else:
            self.auth_store = auth_store

        self.username = username
        self.password = password
        self.plain_password = plain_password
        self.timeout = timeout
        self.ua = UserAgent()

        self._token: Optional[str] = None
        self._sync_lock = threading.Lock()
        self._async_lock = asyncio.Lock()
        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

        if not username or not password:
            logger.warning(
                "KSEIClient initialized without credentials; requests requiring authentication will fail."
            )

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._async_client

    def close(self):
        """Close underlying synchronous HTTP connections."""
        if self._sync_client is not None and not self._sync_client.is_closed:
            self._sync_client.close()

    async def aclose(self):
        """Close underlying asynchronous HTTP connections."""
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    def _build_password_hash_params(self) -> tuple[str, str]:
        if not self.plain_password:
            return self.password, ""

        password_sha1 = hashlib.sha1(self.password.encode()).hexdigest()
        timestamp = int(time.time())
        param = f"{password_sha1}@@!!@@{timestamp}"
        encoded_param = base64.b64encode(param.encode()).decode()
        return password_sha1, encoded_param

    def _hash_password(self, client: httpx.Client) -> str:
        if not self.plain_password:
            return self.password

        _, encoded_param = self._build_password_hash_params()
        url = f"{self.base_url}/activation/generated?param={quote(encoded_param)}"

        try:
            response = client.get(
                url,
                headers={"Referer": self.base_referer, "User-Agent": self.ua.random},
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["pass"]
        except httpx.HTTPStatusError as e:
            raise KSEIAuthError(
                f"Password hash generation failed with HTTP {e.response.status_code}"
            ) from e
        except (KeyError, IndexError, ValueError) as e:
            raise KSEIResponseError(
                f"Unexpected password hash response structure: {e}"
            ) from e
        except httpx.RequestError as e:
            raise KSEINetworkError(
                f"Network error during password hashing: {e}"
            ) from e

    async def _hash_password_async(self, client: httpx.AsyncClient) -> str:
        if not self.plain_password:
            return self.password

        _, encoded_param = self._build_password_hash_params()
        url = f"{self.base_url}/activation/generated?param={quote(encoded_param)}"

        try:
            response = await client.get(
                url,
                headers={"Referer": self.base_referer, "User-Agent": self.ua.random},
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["pass"]
        except httpx.HTTPStatusError as e:
            raise KSEIAuthError(
                f"Password hash generation failed with HTTP {e.response.status_code}"
            ) from e
        except (KeyError, IndexError, ValueError) as e:
            raise KSEIResponseError(
                f"Unexpected password hash response structure: {e}"
            ) from e
        except httpx.RequestError as e:
            raise KSEINetworkError(
                f"Network error during password hashing: {e}"
            ) from e

    def _login(self, client: httpx.Client) -> str:
        if not self.username or not self.password:
            raise KSEIAuthError("Cannot login: KSEI_USERNAME and KSEI_PASSWORD are required")

        hashed_password = self._hash_password(client)
        login_data = {
            "username": self.username,
            "password": hashed_password,
            "id": "1",
            "appType": "web",
        }

        url = f"{self.base_url}/login?lang=id"
        headers = {
            "Referer": self.base_referer,
            "User-Agent": self.ua.random,
            "Content-Type": "application/json",
        }

        logger.debug(f"Logging in user {mask_secret(self.username)}")
        try:
            response = client.post(url, json=login_data, headers=headers)
            response.raise_for_status()
            data = response.json()
            token = data.get("validation")
            if not token:
                raise KSEIAuthError(f"Login failed: missing validation token in response ({data})")

            if self.auth_store:
                self.auth_store.set(self.username, token)

            self._token = token
            logger.info(f"Successfully authenticated {mask_secret(self.username)}")
            return token
        except httpx.HTTPStatusError as e:
            raise KSEIAuthError(f"Authentication failed with HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise KSEINetworkError(f"Network error during authentication: {e}") from e
        except ValueError as e:
            raise KSEIResponseError("Invalid JSON received during authentication") from e

    async def _login_async(self, client: httpx.AsyncClient) -> str:
        if not self.username or not self.password:
            raise KSEIAuthError("Cannot login: KSEI_USERNAME and KSEI_PASSWORD are required")

        hashed_password = await self._hash_password_async(client)
        login_data = {
            "username": self.username,
            "password": hashed_password,
            "id": "1",
            "appType": "web",
        }

        url = f"{self.base_url}/login?lang=id"
        headers = {
            "Referer": self.base_referer,
            "User-Agent": self.ua.random,
            "Content-Type": "application/json",
        }

        logger.debug(f"Logging in user {mask_secret(self.username)} (async)")
        try:
            response = await client.post(url, json=login_data, headers=headers)
            response.raise_for_status()
            data = response.json()
            token = data.get("validation")
            if not token:
                raise KSEIAuthError(f"Login failed: missing validation token in response ({data})")

            if self.auth_store:
                self.auth_store.set(self.username, token)

            self._token = token
            logger.info(f"Successfully authenticated {mask_secret(self.username)}")
            return token
        except httpx.HTTPStatusError as e:
            raise KSEIAuthError(f"Authentication failed with HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise KSEINetworkError(f"Network error during authentication: {e}") from e
        except ValueError as e:
            raise KSEIResponseError("Invalid JSON received during authentication") from e

    def _get_token(self, force_refresh: bool = False) -> str:
        client = self._get_sync_client()
        with self._sync_lock:
            if not force_refresh:
                if self._token:
                    exp = get_expire_time(self._token)
                    if exp and exp > (time.time() + 60):
                        return self._token

                if self.auth_store:
                    token = self.auth_store.get(self.username)
                    if token:
                        exp = get_expire_time(token)
                        if exp and exp > (time.time() + 60):
                            self._token = token
                            return token

            token = self._login(client)
            return token

    async def _get_token_async(self, force_refresh: bool = False) -> str:
        client = self._get_async_client()
        async with self._async_lock:
            if not force_refresh:
                if self._token:
                    exp = get_expire_time(self._token)
                    if exp and exp > (time.time() + 60):
                        return self._token

                if self.auth_store:
                    token = self.auth_store.get(self.username)
                    if token:
                        exp = get_expire_time(token)
                        if exp and exp > (time.time() + 60):
                            self._token = token
                            return token

            token = await self._login_async(client)
            return token

    def get(self, path: str, retry_on_401: bool = True) -> Union[Dict[str, Any], List[Any]]:
        """
        Make an authenticated GET request to the KSEI API.
        """
        if not path.startswith("/"):
            path = f"/{path}"

        client = self._get_sync_client()
        token = self._get_token()
        url = f"{self.base_url}{path}"

        headers = {
            "Referer": self.base_referer,
            "User-Agent": self.ua.random,
            "Authorization": f"Bearer {token}",
        }

        try:
            response = client.get(url, headers=headers)
            if response.status_code == 401 and retry_on_401:
                logger.warning("Received 401 Unauthorized; refreshing token and retrying...")
                token = self._get_token(force_refresh=True)
                headers["Authorization"] = f"Bearer {token}"
                response = client.get(url, headers=headers)

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise KSEIAuthError(f"Unauthorized (401) accessing {path}") from e
            raise KSEIResponseError(
                f"HTTP {e.response.status_code} error accessing {path}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise KSEINetworkError(f"Network error requesting {path}: {e}") from e
        except ValueError as e:
            raise KSEIResponseError(f"Invalid JSON received from {path}") from e

    async def get_async(
        self, path: str, retry_on_401: bool = True
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Make an authenticated asynchronous GET request to the KSEI API.
        """
        if not path.startswith("/"):
            path = f"/{path}"

        client = self._get_async_client()
        token = await self._get_token_async()
        url = f"{self.base_url}{path}"

        headers = {
            "Referer": self.base_referer,
            "User-Agent": self.ua.random,
            "Authorization": f"Bearer {token}",
        }

        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 401 and retry_on_401:
                logger.warning("Received 401 Unauthorized; refreshing token and retrying (async)...")
                token = await self._get_token_async(force_refresh=True)
                headers["Authorization"] = f"Bearer {token}"
                response = await client.get(url, headers=headers)

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise KSEIAuthError(f"Unauthorized (401) accessing {path}") from e
            raise KSEIResponseError(
                f"HTTP {e.response.status_code} error accessing {path}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise KSEINetworkError(f"Network error requesting {path}: {e}") from e
        except ValueError as e:
            raise KSEIResponseError(f"Invalid JSON received from {path}") from e

    def get_portfolio_summary(self) -> Union[Dict[str, Any], List[Any]]:
        return self.get("/myportofolio/summary")

    def get_cash_balances(self) -> Union[Dict[str, Any], List[Any]]:
        return self.get("/myportofolio/summary-detail/kas")

    def get_equity_balances(self) -> Union[Dict[str, Any], List[Any]]:
        return self.get("/myportofolio/summary-detail/ekuitas")

    def get_mutual_fund_balances(self) -> Union[Dict[str, Any], List[Any]]:
        return self.get("/myportofolio/summary-detail/reksadana")

    def get_bond_balances(self) -> Union[Dict[str, Any], List[Any]]:
        return self.get("/myportofolio/summary-detail/obligasi")

    def get_other_balances(self) -> Union[Dict[str, Any], List[Any]]:
        return self.get("/myportofolio/summary-detail/lainnya")

    def get_global_identity(self) -> Union[Dict[str, Any], List[Any]]:
        return self.get("/myaccount/global-identity/")

    async def get_all_portfolios_async(self) -> Dict[str, Optional[Union[Dict[str, Any], List[Any]]]]:
        """
        Asynchronously fetch all portfolio types in parallel.
        """
        portfolio_types = {
            "cash": "/myportofolio/summary-detail/kas",
            "equity": "/myportofolio/summary-detail/ekuitas",
            "mutual_fund": "/myportofolio/summary-detail/reksadana",
            "bond": "/myportofolio/summary-detail/obligasi",
            "other": "/myportofolio/summary-detail/lainnya",
        }

        logger.info("Fetching all portfolio types concurrently")
        tasks = []
        for portfolio_type, path in portfolio_types.items():
            task = asyncio.create_task(self.get_async(path), name=portfolio_type)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        portfolio_data: Dict[str, Optional[Union[Dict[str, Any], List[Any]]]] = {}
        for task, result in zip(tasks, results):
            portfolio_type = task.get_name()
            if isinstance(result, Exception):
                logger.error(f"Error fetching {portfolio_type}: {result}")
                portfolio_data[portfolio_type] = None
            else:
                portfolio_data[portfolio_type] = result

        return portfolio_data

    def __repr__(self) -> str:
        return f"KSEIClient(username={mask_secret(self.username)}, auth_store={self.auth_store})"
