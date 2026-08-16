import os
import sys
import json
import logging
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from ksei.client import KSEIClient
from ksei.exceptions import KSEIAuthError

load_dotenv()

# Route all logs strictly to stderr to prevent stdout JSON-RPC message corruption
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("ksei.mcp")

# Initialize FastMCP application
mcp = FastMCP(
    name="ksei-server",
    instructions="MCP server for retrieving Indonesian securities portfolio data from AKSes KSEI.",
)

_ksei_client: Optional[KSEIClient] = None


def get_ksei_client() -> KSEIClient:
    """Retrieve or initialize the singleton KSEIClient using environment variables."""
    global _ksei_client
    if _ksei_client is not None:
        return _ksei_client

    username = os.getenv("KSEI_USERNAME")
    password = os.getenv("KSEI_PASSWORD")

    if not username or not password:
        raise KSEIAuthError(
            "Missing credentials: KSEI_USERNAME and KSEI_PASSWORD environment variables must be configured."
        )

    _ksei_client = KSEIClient(username=username, password=password)
    return _ksei_client


# ==========================================
# MCP Tools
# ==========================================


@mcp.tool()
async def get_portfolio_summary() -> Any:
    """Get high-level summary of all portfolio holdings and balances from AKSes KSEI."""
    client = get_ksei_client()
    return client.get_portfolio_summary()


@mcp.tool()
async def get_cash_balances() -> Any:
    """Get detailed cash (Rekening Dana Nasabah / RDN) balances across securities accounts."""
    client = get_ksei_client()
    return client.get_cash_balances()


@mcp.tool()
async def get_equity_balances() -> Any:
    """Get detailed Indonesian stock holdings (Saham) including shares, market value, and prices."""
    client = get_ksei_client()
    return client.get_equity_balances()


@mcp.tool()
async def get_mutual_fund_balances() -> Any:
    """Get detailed mutual fund holdings (Reksadana) including unit counts and NAV values."""
    client = get_ksei_client()
    return client.get_mutual_fund_balances()


@mcp.tool()
async def get_bond_balances() -> Any:
    """Get bond and government securities holdings (Obligasi / SBN)."""
    client = get_ksei_client()
    return client.get_bond_balances()


@mcp.tool()
async def get_other_balances() -> Any:
    """Get other financial instruments and investment balances."""
    client = get_ksei_client()
    return client.get_other_balances()


@mcp.tool()
async def get_global_identity() -> Any:
    """Get KSEI account holder identity, SID, and investor profile details."""
    client = get_ksei_client()
    return client.get_global_identity()


@mcp.tool()
async def get_all_portfolios() -> Dict[str, Any]:
    """Fetch all portfolio holdings (cash, equities, mutual funds, bonds, other) in parallel."""
    client = get_ksei_client()
    return await client.get_all_portfolios_async()


# ==========================================
# MCP Resources
# ==========================================


@mcp.resource("ksei://portfolio/summary")
async def resource_portfolio_summary() -> str:
    """Overview of all portfolio holdings and balances."""
    client = get_ksei_client()
    return json.dumps(client.get_portfolio_summary(), indent=2, ensure_ascii=False)


@mcp.resource("ksei://portfolio/cash")
async def resource_cash_balances() -> str:
    """Detailed cash balances across securities companies."""
    client = get_ksei_client()
    return json.dumps(client.get_cash_balances(), indent=2, ensure_ascii=False)


@mcp.resource("ksei://portfolio/equity")
async def resource_equity_balances() -> str:
    """Stock and equity holdings details."""
    client = get_ksei_client()
    return json.dumps(client.get_equity_balances(), indent=2, ensure_ascii=False)


@mcp.resource("ksei://portfolio/mutual-fund")
async def resource_mutual_fund_balances() -> str:
    """Mutual fund investment details."""
    client = get_ksei_client()
    return json.dumps(client.get_mutual_fund_balances(), indent=2, ensure_ascii=False)


@mcp.resource("ksei://portfolio/bond")
async def resource_bond_balances() -> str:
    """Bond and fixed income securities."""
    client = get_ksei_client()
    return json.dumps(client.get_bond_balances(), indent=2, ensure_ascii=False)


@mcp.resource("ksei://account/identity")
async def resource_account_identity() -> str:
    """Account holder identity and profile information."""
    client = get_ksei_client()
    return json.dumps(client.get_global_identity(), indent=2, ensure_ascii=False)



def run():
    """Entry point for running the MCP server with stdio transport."""
    mcp.run(transport="stdio")


def main():
    run()


if __name__ == "__main__":
    run()
