"""Utility script for seeding example links into DynamoDB."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

import boto3

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from utils.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed AuroraLink Forge sample data")
    parser.add_argument("--owner", default="sample", help="Owner label for seeded links")
    parser.add_argument("--count", type=int, default=3, help="How many links to create")
    return parser.parse_args()


def seed_links(owner: str, count: int) -> None:
    config = load_config()
    client = boto3.client("dynamodb", region_name=config.region_name)
    now = int(dt.datetime.utcnow().timestamp())

    for idx in range(count):
        code = f"demo{idx+1}"
        item = {
            "PK": {"S": f"LINK#{code}"},
            "SK": {"S": "METADATA"},
            "code": {"S": code},
            "destination": {"S": f"https://example.com/{code}"},
            "createdAt": {"S": dt.datetime.utcnow().isoformat() + "Z"},
            "expiresAt": {"N": str(now + config.default_ttl_seconds)},
            "clicks": {"N": "0"},
            "owner": {"S": owner},
        }
        client.put_item(TableName=config.table_name, Item=item)
        print(json.dumps({"code": code, "destination": item["destination"]["S"]}))


def main() -> None:
    args = parse_args()
    seed_links(owner=args.owner, count=args.count)


if __name__ == "__main__":
    main()
