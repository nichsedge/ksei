
import time

import hashlib
import base64
from urllib.parse import quote
import requests
import jwt
from fake_useragent import UserAgent
import asyncio
import aiohttp
from typing import Any, Dict, List, Optional

def get_expire_time(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("exp")
    except:
        return None

class KSEIClient:
    def __init__(self, auth_store=None, username="", password="", plain_password=True):
        self.base_url = "https://akses.ksei.co.id/service"
        self.base_referer = "https://akses.ksei.co.id"
        self.auth_store = auth_store
        self.username = username
        self.password = password
        self.plain_password = plain_password
        self.ua = UserAgent()

    def _hash_password(self):
        if not self.plain_password:
            return self.password

        password_sha1 = hashlib.sha1(self.password.encode()).hexdigest()
        timestamp = int(time.time())
        param = f"{password_sha1}@@!!@@{timestamp}"
        encoded_param = base64.b64encode(param.encode()).decode()

        url = f"{self.base_url}/activation/generated?param={quote(encoded_param)}"

        response = requests.get(
            url, headers={"Referer": self.base_referer, "User-Agent": self.ua.random}
        )
        response.raise_for_status()

        data = response.json()
        return data["data"][0]["pass"]

    def _login(self):
        hashed_password = self._hash_password()

        login_data = {
            "username": self.username,
            "password": hashed_password,
            "id": "1",
            "appType": "web",
        }

        response = requests.post(
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

    def _get_token(self):
        if not self.auth_store:
            return self._login()

        token = self.auth_store.get(self.username)
        if not token:
            return self._login()

        expire_time = get_expire_time(token)
        if not expire_time or expire_time < time.time():
            return self._login()

        return token

    def get(self, path):
        token = self._get_token()

        response = requests.get(
            f"{self.base_url}{path}",
            headers={
                "Referer": self.base_referer,
                "User-Agent": self.ua.random,
                "Authorization": f"Bearer {token}",
            },
        )
        response.raise_for_status()
        return response.json()

    def get_portfolio_summary(self):
        return self.get("/myportofolio/summary")

    def get_cash_balances(self):
        return self.get("/myportofolio/summary-detail/kas")

    def get_equity_balances(self):
        return self.get("/myportofolio/summary-detail/ekuitas")

    def get_mutual_fund_balances(self):
        return self.get("/myportofolio/summary-detail/reksadana")

    def get_bond_balances(self):
        return self.get("/myportofolio/summary-detail/obligasi")

    def get_other_balances(self):
        return self.get("/myportofolio/summary-detail/lainnya")

    def get_global_identity(self):
        return self.get("/myaccount/global-identity/")

    async def get_async(self, session, path):
        token = self._get_token()

        async with session.get(
            f"{self.base_url}{path}",
            headers={
                "Referer": self.base_referer,
                "User-Agent": self.ua.random,
                "Authorization": f"Bearer {token}",
            },
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_all_portfolios_async(self):
        portfolio_types = {
            "cash": "/myportofolio/summary-detail/kas",
            "equity": "/myportofolio/summary-detail/ekuitas",
            "mutual_fund": "/myportofolio/summary-detail/reksadana",
            "bond": "/myportofolio/summary-detail/obligasi",
            "other": "/myportofolio/summary-detail/lainnya",
        }

        async with aiohttp.ClientSession() as session:
            tasks = []
            for portfolio_type, path in portfolio_types.items():
                task = asyncio.create_task(
                    self.get_async(session, path), name=portfolio_type
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            portfolio_data = {}
            for task, result in zip(tasks, results):
                portfolio_type = task.get_name()
                if isinstance(result, Exception):
                    print(f"Error fetching {portfolio_type}: {result}")
                    portfolio_data[portfolio_type] = None
                else:
                    portfolio_data[portfolio_type] = result

            return portfolio_data