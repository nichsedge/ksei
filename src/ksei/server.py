import json
import os
import asyncio
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)

from ksei.client import KSEIClient
from ksei.utils import FileAuthStore

load_dotenv()

# Initialize the MCP server
server = Server("ksei-server")

_ksei_client: Optional[KSEIClient] = None


def get_ksei_client() -> KSEIClient:
    global _ksei_client
    if _ksei_client is not None:
        return _ksei_client

    username = os.getenv("KSEI_USERNAME")
    password = os.getenv("KSEI_PASSWORD")
    auth_path = os.getenv("KSEI_AUTH_PATH", "./data")

    if not username or not password:
        raise ValueError(
            "KSEI_USERNAME and KSEI_PASSWORD environment variables must be set"
        )

    auth_store = FileAuthStore(directory=auth_path)
    _ksei_client = KSEIClient(auth_store=auth_store, username=username, password=password)
    return _ksei_client


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available KSEI resources."""
    return [
        Resource(
            uri="ksei://portfolio/summary",
            name="Portfolio Summary",
            description="Overview of all portfolio holdings and balances",
            mimeType="application/json",
        ),
        Resource(
            uri="ksei://portfolio/cash",
            name="Cash Balances",
            description="Detailed cash balances across securities companies",
            mimeType="application/json",
        ),
        Resource(
            uri="ksei://portfolio/equity",
            name="Equity Holdings",
            description="Stock and equity holdings details",
            mimeType="application/json",
        ),
        Resource(
            uri="ksei://portfolio/mutual-fund",
            name="Mutual Fund Holdings",
            description="Mutual fund investment details",
            mimeType="application/json",
        ),
        Resource(
            uri="ksei://portfolio/bond",
            name="Bond Holdings",
            description="Bond and fixed income securities",
            mimeType="application/json",
        ),
        Resource(
            uri="ksei://portfolio/other",
            name="Other Holdings",
            description="Other financial instruments and investments",
            mimeType="application/json",
        ),
        Resource(
            uri="ksei://account/identity",
            name="Account Identity",
            description="Account holder identity and profile information",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific KSEI resource."""
    try:
        client = get_ksei_client()
        if uri == "ksei://portfolio/summary":
            data = client.get_portfolio_summary()
        elif uri == "ksei://portfolio/cash":
            data = client.get_cash_balances()
        elif uri == "ksei://portfolio/equity":
            data = client.get_equity_balances()
        elif uri == "ksei://portfolio/mutual-fund":
            data = client.get_mutual_fund_balances()
        elif uri == "ksei://portfolio/bond":
            data = client.get_bond_balances()
        elif uri == "ksei://portfolio/other":
            data = client.get_other_balances()
        elif uri == "ksei://account/identity":
            data = client.get_global_identity()
        else:
            raise ValueError(f"Unknown resource URI: {uri}")

        return json.dumps(data, indent=2, ensure_ascii=False)

    except Exception as e:
        raise RuntimeError(f"Failed to fetch resource {uri}: {str(e)}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available KSEI tools."""
    return [
        Tool(
            name="get_portfolio_summary",
            description="Get a summary of all portfolio holdings and balances",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_cash_balances",
            description="Get detailed cash balances across all securities companies",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_equity_balances",
            description="Get detailed equity/stock holdings",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_mutual_fund_balances",
            description="Get mutual fund investment details",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_bond_balances",
            description="Get bond and fixed income securities details",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_other_balances",
            description="Get other financial instruments and investments",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_global_identity",
            description="Get account holder identity and profile information",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_all_portfolios",
            description="Get all portfolio data concurrently (cash, equity, mutual funds, bonds, other)",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool calls for KSEI operations."""
    try:
        client = get_ksei_client()
        if name == "get_portfolio_summary":
            result = client.get_portfolio_summary()
        elif name == "get_cash_balances":
            result = client.get_cash_balances()
        elif name == "get_equity_balances":
            result = client.get_equity_balances()
        elif name == "get_mutual_fund_balances":
            result = client.get_mutual_fund_balances()
        elif name == "get_bond_balances":
            result = client.get_bond_balances()
        elif name == "get_other_balances":
            result = client.get_other_balances()
        elif name == "get_global_identity":
            result = client.get_global_identity()
        elif name == "get_all_portfolios":
            result = await client.get_all_portfolios_async()
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [
            TextContent(
                type="text", text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]

    except Exception as e:
        return [TextContent(type="text", text=f"Error calling tool {name}: {str(e)}")]


async def main():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ksei-server",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
