# KSEI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client library and **Model Context Protocol (MCP)** server for accessing your [AKSes KSEI](https://akses.ksei.co.id) (Acuan Kepemilikan Sekuritas Kustodian Sentral Efek Indonesia) portfolio data.

Retrieve complete Indonesian securities portfolio information:
* 💵 Cash balances
* 📈 Equity holdings
* 📊 Mutual funds
* 📜 Bonds (Obligasi & SBN)
* 💼 Other investment instruments
* 👤 Account identity

---

## 🔧 Prerequisites

* Python 3.11 or higher
* Valid KSEI account credentials
* [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (recommended for fast package management)

---

## ⚙️ Configuration

Set your KSEI credentials via environment variables or a `.env` file:

```bash
export KSEI_USERNAME="your_ksei_username"
export KSEI_PASSWORD="your_ksei_password"
export KSEI_AUTH_PATH="./data"  # Optional, path to cache auth tokens (defaults to ./data)
```

---

## 🚀 Usage

### 1. As a Python Library

```python
import asyncio
from ksei import KSEIClient, FileAuthStore

# Initialize client
auth_store = FileAuthStore(directory="./data")
client = KSEIClient(auth_store=auth_store, username="your_username", password="your_password")

# Synchronous usage
summary = client.get_portfolio_summary()
cash = client.get_cash_balances()
equities = client.get_equity_balances()
funds = client.get_mutual_fund_balances()
bonds = client.get_bond_balances()

# Asynchronous usage (fast parallel fetch)
async def main():
    all_portfolios = await client.get_all_portfolios_async()
    print(all_portfolios)

asyncio.run(main())
```

---

### 2. As an MCP Server (for AI Assistants)

#### Quick Run with `uvx`

```bash
# Run directly with uvx
uvx ksei-mcp

# Or run from local checkout
uvx --from . ksei-mcp
```

#### MCP Client Configuration

Add this configuration to your MCP client (Claude Desktop, Cursor, Gemini CLI, etc.):

```json
{
  "mcpServers": {
    "ksei": {
      "type": "stdio",
      "command": "uvx",
      "args": ["ksei-mcp"],
      "env": {
        "KSEI_USERNAME": "your_ksei_username",
        "KSEI_PASSWORD": "your_ksei_password",
        "KSEI_AUTH_PATH": "./data"
      }
    }
  }
}
```

---

### 3. Example Script (Fetch and Dump)

Run the included example script to dump all portfolio holdings to a JSON file:

```bash
uv run examples/fetch_and_dump_portfolios.py
```

---

## 🧪 Testing with MCP Inspector

For local MCP debugging:

```bash
npx @modelcontextprotocol/inspector uv run ksei-mcp
```

---

## 🔐 Security & Privacy

* **Credentials**: Never commit credentials to version control. Use `.env` or system environment variables.
* **Token Caching**: JWT tokens are cached locally as JSON files until expiration to minimize login requests.
* **Secure Transport**: All requests communicate with official KSEI endpoints via HTTPS.

---

## 📄 License

Licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

## ⚠️ Disclaimer

This is an **unofficial client** for educational and personal use only. It is not affiliated with or endorsed by PT Kustodian Sentral Efek Indonesia (KSEI).

### Acknowledgement
Adapted and inspired by [chickenzord/goksei](https://github.com/chickenzord/goksei).
