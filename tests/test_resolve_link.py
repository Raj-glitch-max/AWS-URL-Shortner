import json
import pathlib
import sys
from types import SimpleNamespace

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from handlers import resolve_link


class Repo:
    def __init__(self, item=None):
        self.item = item or {
            "code": "abc",
            "destination": "https://example.com",
            "expiresAt": 9999999999,
            "clicks": 0,
        }
        self.updated = self.item.copy()

    def get_link(self, code):
        return self.item if code == self.item["code"] else None

    def increment_clicks(self, code):
        if code != self.item["code"]:
            return None
        self.updated["clicks"] = self.item.get("clicks", 0) + 1
        return self.updated

    def save_click(self, item):
        self.saved = item


def test_resolve_link_success(monkeypatch):
    repo = Repo()
    monkeypatch.setattr(resolve_link, "get_repository", lambda: repo)
    event = {"pathParameters": {"code": "abc"}}
    response = resolve_link.handler(event, SimpleNamespace(aws_request_id="req"))
    assert response["statusCode"] == 302
    assert response["headers"]["Location"] == "https://example.com"


def test_resolve_link_not_found(monkeypatch):
    repo = Repo()
    repo.item = None
    monkeypatch.setattr(resolve_link, "get_repository", lambda: repo)
    event = {"pathParameters": {"code": "missing"}}
    response = resolve_link.handler(event, SimpleNamespace(aws_request_id="req"))
    body = json.loads(response["body"])
    assert response["statusCode"] == 404
    assert body["error"]["code"] == "NOT_FOUND"
