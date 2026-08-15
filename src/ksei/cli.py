import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
import datetime
from dotenv import load_dotenv

from ksei.client import KSEIClient
from ksei.utils import FileAuthStore, mask_secret
from ksei.exceptions import KSEIError


def dump_cmd(args):
    """Fetch and dump portfolio to JSON."""
    username = args.username or os.getenv("KSEI_USERNAME")
    password = args.password or os.getenv("KSEI_PASSWORD")
    auth_path = args.auth_path or os.getenv("KSEI_AUTH_PATH", "./data")
    output_dir = (
        args.output
        or os.getenv("KSEI_OUTPUT_DIR")
        or os.getenv("PORTFOLIO_DATA_DIR")
        or os.getenv("DATA_DIR")
        or "./data"
    )

    if not username or not password:
        print("❌ Error: KSEI_USERNAME and KSEI_PASSWORD must be provided via flags or environment variables.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching KSEI portfolios for {mask_secret(username)}...", file=sys.stderr)
    auth_store = FileAuthStore(directory=auth_path)
    client = KSEIClient(auth_store=auth_store, username=username, password=password)

    data = asyncio.run(client.get_all_portfolios_async())
    
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    out_file = out_dir_path / f"{current_date}_raw_ksei.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved portfolio data to: {out_file.resolve()}", file=sys.stderr)


def mcp_cmd(args):
    """Run MCP server."""
    from ksei.server import run
    run()


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        prog="ksei",
        description="KSEI CLI and MCP Tool",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Dump command
    dump_parser = subparsers.add_parser("dump", help="Fetch and save portfolio data to JSON")
    dump_parser.add_argument("-u", "--username", help="KSEI username")
    dump_parser.add_argument("-p", "--password", help="KSEI password")
    dump_parser.add_argument("-a", "--auth-path", help="Path to cache auth tokens")
    dump_parser.add_argument("-o", "--output", help="Output directory for JSON file")
    dump_parser.set_defaults(func=dump_cmd)

    # MCP command
    mcp_parser = subparsers.add_parser("mcp", help="Run KSEI Model Context Protocol (MCP) server")
    mcp_parser.set_defaults(func=mcp_cmd)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
