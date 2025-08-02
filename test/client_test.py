from ksei.client import KSEIClient
from ksei.utils import FileAuthStore

import os

# Initialize KSEI client
username = os.getenv("KSEI_USERNAME")
password = os.getenv("KSEI_PASSWORD")
auth_path = os.getenv("KSEI_AUTH_PATH", "./auth")

if not username or not password:
    raise ValueError(
        "KSEI_USERNAME and KSEI_PASSWORD environment variables must be set"
    )

auth_store = FileAuthStore(directory=auth_path)
ksei_client = KSEIClient(auth_store=auth_store, username=username, password=password)


async def main():
    res = await ksei_client.get_all_portfolios_async()
    
    import json
    from pathlib import Path

    # Ensure auth_path directory exists
    Path(auth_path).mkdir(parents=True, exist_ok=True)

    # Serialize and write the result to JSON under auth_path
    out_file = Path(auth_path) / "ksei_portfolios.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    print(f"Wrote portfolios to: {out_file.resolve()}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

