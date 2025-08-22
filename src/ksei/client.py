
import time
import hashlib
import base64
from urllib.parse import quote
import jwt
from fake_useragent import UserAgent
import asyncio
import httpx
from typing import Any, Dict, List, Optional, Union


def get_expire_time(token: str) -> Optional[int]:
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("exp")
    except jwt.DecodeError:
        return None


class KSEIClient:
    def __init__(
        self,
        auth_store=None,
        username: str = "",
        password: str = "",
        plain_password: bool = True,
        timeout: float = 30.0,
    ):
        self.base_url = "https://akses.ksei.co.id/service"
        self.base_referer = "https://akses.ksei.co.id"
        self.auth_store = auth_store
        self.username = username
        self.password = password
        self.plain_password = plain_password
        self.ua = UserAgent()
        self.timeout = timeout
        self._token: Optional[str] = None
        self._lock = asyncio.Lock()
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def _hash_password(self, client: httpx.Client) -> str:
        if not self.plain_password:
            return self.password

        password_sha1 = hashlib.sha1(self.password.encode()).hexdigest()
        timestamp = int(time.time())
        param = f"{password_sha1}@@!!@@{timestamp}"
        encoded_param = base64.b64encode(param.encode()).decode()

        url = f"{self.base_url}/activation/generated?param={quote(encoded_param)}"

        response = client.get(
            url, headers={"Referer": self.base_referer, "User-Agent": self.ua.random}
        )
        response.raise_for_status()

        data = response.json()
        return data["data"][0]["pass"]

    async def _hash_password_async(self, client: httpx.AsyncClient) -> str:
        if not self.plain_password:
            return self.password

        password_sha1 = hashlib.sha1(self.password.encode()).hexdigest()
        timestamp = int(time.time())
        param = f"{password_sha1}@@!!@@{timestamp}"
        encoded_param = base64.b64encode(param.encode()).decode()

        url = f"{self.base_url}/activation/generated?param={quote(encoded_param)}"

        response = await client.get(
            url, headers={"Referer": self.base_referer, "User-Agent": self.ua.random}
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["pass"]

    def _login(self, client: httpx.Client) -> str:
        hashed_password = self._hash_password(client)

        login_data = {
            "username": self.username,
            "password": hashed_password,
            "id": "1",
            "appType": "web",
        }

        response = client.post(
            f"{self.base_url}/login?lang=id",
            json=login_data,
            headers={
                "Referer": self.base_referer,
                "User-Agent": self.ua.random,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()

        token = response.json()["validation"]

        if self.auth_store:
            self.auth_store.set(self.username, token)

        return token

    async def _login_async(self, client: httpx.AsyncClient) -> str:
        hashed_password = await self._hash_password_async(client)

        login_data = {
            "username": self.username,
            "password": hashed_password,
            "id": "1",
            "appType": "web",
        }

        response = await client.post(
            f"{self.base_url}/login?lang=id",
            json=login_data,
            headers={
                "Referer": self.base_referer,
                "User-Agent": self.ua.random,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()
        token = data["validation"]

        if self.auth_store:
            self.auth_store.set(self.username, token)

        return token

    def _get_token(self) -> str:
        client = self._get_client()
        if not self.auth_store:
            return self._login(client)

        token = self.auth_store.get(self.username)
        if not token:
            return self._login(client)

        expire_time = get_expire_time(token)
        if not expire_time or expire_time < time.time():
            return self._login(client)

        return token

    async def _get_token_async(self, client: httpx.AsyncClient) -> str:
        if self._token:
            expire_time = get_expire_time(self._token)
            if expire_time and expire_time > time.time():
                return self._token

        async with self._lock:
            # Check again in case another task just refreshed the token
            if self._token:
                expire_time = get_expire_time(self._token)
                if expire_time and expire_time > time.time():
                    return self._token

            token = None
            if self.auth_store:
                token = self.auth_store.get(self.username)

            if token:
                expire_time = get_expire_time(token)
                if expire_time and expire_time > time.time():
                    self._token = token
                    return token

            self._token = await self._login_async(client)
            return self._token

    def get(self, path: str) -> Union[Dict, List]:
        client = self._get_client()
        token = self._get_token()

        response = client.get(
            f"{self.base_url}{path}",
            headers={
                "Referer": self.base_referer,
                "User-Agent": self.ua.random,
                "Authorization": f"Bearer {token}",
            },
        )
        response.raise_for_status()
        return response.json()

    def get_portfolio_summary(self) -> Union[Dict, List]:
        return self.get("/myportofolio/summary")

    def get_cash_balances(self) -> Union[Dict, List]:
        return self.get("/myportofolio/summary-detail/kas")

    def get_equity_balances(self) -> Union[Dict, List]:
        return self.get("/myportofolio/summary-detail/ekuitas")

    def get_mutual_fund_balances(self) -> Union[Dict, List]:
        return self.get("/myportofolio/summary-detail/reksadana")

    def get_bond_balances(self) -> Union[Dict, List]:
        return self.get("/myportofolio/summary-detail/obligasi")

    def get_other_balances(self) -> Union[Dict, List]:
        return self.get("/myportofolio/summary-detail/lainnya")

    def get_global_identity(self) -> Union[Dict, List]:
        return self.get("/myaccount/global-identity/")

    async def get_async(
        self, client: httpx.AsyncClient, path: str
    ) -> Union[Dict, List]:
        token = await self._get_token_async(client)

        response = await client.get(
            f"{self.base_url}{path}",
            headers={
                "Referer": self.base_referer,
                "User-Agent": self.ua.random,
                "Authorization": f"Bearer {token}",
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_all_portfolios_async(self) -> Dict[str, Optional[Union[Dict, List]]]:
        portfolio_types = {
            "cash": "/myportofolio/summary-detail/kas",
            "equity": "/myportofolio/summary-detail/ekuitas",
            "mutual_fund": "/myportofolio/summary-detail/reksadana",
            "bond": "/myportofolio/summary-detail/obligasi",
            "other": "/myportofolio/summary-detail/lainnya",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = []
            for portfolio_type, path in portfolio_types.items():
                task = asyncio.create_task(
                    self.get_async(client, path), name=portfolio_type
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

        portfolio_data: Dict[str, Optional[Union[Dict, List]]] = {}
        for task, result in zip(tasks, results):
            portfolio_type = task.get_name()
            if isinstance(result, Exception):
                print(f"Error fetching {portfolio_type}: {result!r}")
                portfolio_data[portfolio_type] = None
            else:
                portfolio_data[portfolio_type] = result

        return portfolio_data