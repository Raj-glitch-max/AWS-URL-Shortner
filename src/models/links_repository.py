"""Data access layer for AuroraLink Forge."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from utils.config import AppConfig

logger = logging.getLogger("auroralink")


class LinksRepository:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._dynamodb = boto3.resource("dynamodb", region_name=config.region_name)
        self._table = self._dynamodb.Table(config.table_name)

    @staticmethod
    def _pk(code: str) -> str:
        return f"LINK#{code}"

    def next_counter(self) -> int:
        client = boto3.client("dynamodb", region_name=self._config.region_name)
        response = client.update_item(
            TableName=self._config.table_name,
            Key={"PK": {"S": "COUNTER#GLOBAL"}, "SK": {"S": "STATE"}},
            UpdateExpression="SET counter = if_not_exists(counter, :start) + :inc",
            ExpressionAttributeValues={":inc": {"N": "1"}, ":start": {"N": "0"}},
            ReturnValues="UPDATED_NEW",
        )
        return int(response["Attributes"]["counter"]["N"])

    def create_link(
        self,
        code: str,
        destination: str,
        owner: str,
        ttl_seconds: int,
    ) -> Dict[str, Any]:
        expires_at = int(dt.datetime.utcnow().timestamp()) + ttl_seconds
        item = {
            "PK": self._pk(code),
            "SK": "METADATA",
            "code": code,
            "destination": destination,
            "createdAt": dt.datetime.utcnow().isoformat() + "Z",
            "expiresAt": expires_at,
            "clicks": 0,
            "owner": owner,
        }
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ValueError("Alias already exists") from exc
            raise
        return item

    def get_link(self, code: str) -> Optional[Dict[str, Any]]:
        response = self._table.get_item(Key={"PK": self._pk(code), "SK": "METADATA"})
        return response.get("Item")

    def increment_clicks(self, code: str) -> Optional[Dict[str, Any]]:
        try:
            response = self._table.update_item(
                Key={"PK": self._pk(code), "SK": "METADATA"},
                UpdateExpression="SET clicks = clicks + :inc",
                ExpressionAttributeValues={":inc": 1},
                ReturnValues="ALL_NEW",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None
            raise
        return response.get("Attributes")

    def purge_expired(self, now_ts: int) -> int:
        response = self._table.scan(
            FilterExpression="expiresAt < :now",
            ExpressionAttributeValues={":now": now_ts},
            Limit=self._config.cleanup_batch_size,
        )
        items = response.get("Items", [])
        with self._table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
        if items:
            logger.info("expired_links_purged", extra={"count": len(items)})
        return len(items)

    def save_click(self, item: Dict[str, Any]) -> None:
        logger.info("click_recorded", extra={"code": item["code"], "clicks": item["clicks"]})

    def get_stats(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get_link(code)
