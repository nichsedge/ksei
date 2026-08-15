# KSEI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client library and **Model Context Protocol (MCP)** server for accessing your [AKSes KSEI](https://akses.ksei.co.id) (Acuan Kepemilikan Sekuritas Kustodian Sentral Efek Indonesia) portfolio data.

Retrieve complete Indonesian securities portfolio information:
* 💵 Cash balances (RDN)
* 📈 Equity holdings (Saham)
* 📊 Mutual funds (Reksadana)
* 📜 Bonds (Obligasi & SBN)
* 💼 Other investment instruments
* 👤 Account identity & SID

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

# Optional: Override token cache location (defaults automatically to ~/.cache/ksei)
# export KSEI_AUTH_PATH="/custom/path"
```

---

## 🚀 Usage

### 1. As a Python Library

Tokens are automatically cached in `~/.cache/ksei` with restricted `0o700`/`0o600` permissions.

```python
import asyncio
from ksei import KSEIClient

# Initialize client (no auth_store boilerplate needed!)
client = KSEIClient(username="your_username", password="your_password")

# Synchronous usage
summary = client.get_portfolio_summary()
cash = client.get_cash_balances()
equities = client.get_equity_balances()
funds = client.get_mutual_fund_balances()
bonds = client.get_bond_balances()

# Asynchronous usage (fast parallel fetch)
async def main():
    async with KSEIClient(username="your_username", password="your_password") as client:
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
        "KSEI_PASSWORD": "your_ksei_password"
      }
    }
  }
}
```

---

### 3. CLI Commands

```bash
# Start MCP server
uv run ksei mcp

# Fetch and dump raw portfolio JSON
uv run ksei dump --output ./data
```

---

## 🧪 Testing with MCP Inspector

For local MCP debugging:

```bash
npx @modelcontextprotocol/inspector uv run ksei-mcp
```

---

## 🔐 Security & Privacy

* **Zero Boilerplate Cache**: Tokens are cached automatically in `~/.cache/ksei` (XDG standard) with user-only permissions (`0o700` directory, `0o600` files).
* **Secret Protection**: Passwords and tokens are never logged or exposed in `__repr__` or unhandled exceptions.
* **Auto 401 Recovery**: The client transparently refreshes expired tokens on 401 Unauthorized responses.
* **Secure Transport**: All requests communicate with official KSEI endpoints via HTTPS.

---

## 📄 License

Licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

## ⚠️ Disclaimer

This is an **unofficial client** for educational and personal use only. It is not affiliated with or endorsed by PT Kustodian Sentral Efek Indonesia (KSEI).

### Acknowledgement
Adapted and inspired by [chickenzord/goksei](https://github.com/chickenzord/goksei).
