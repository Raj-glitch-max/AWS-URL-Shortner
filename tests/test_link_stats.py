import json
import pathlib
import sys
from types import SimpleNamespace

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from handlers import link_stats


class Repo:
    def __init__(self):
        self.item = {
            "code": "abc",
            "destination": "https://example.com",
            "clicks": 5,
            "createdAt": "2020-01-01T00:00:00Z",
            "expiresAt": 9999999999,
        }

    def get_stats(self, code):
        return self.item if code == "abc" else None


def test_link_stats_success(monkeypatch):
    repo = Repo()
    monkeypatch.setattr(link_stats, "get_repository", lambda: repo)
    event = {"pathParameters": {"code": "abc"}}
    response = link_stats.handler(event, SimpleNamespace())
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["clicks"] == 5


def test_link_stats_not_found(monkeypatch):
    repo = Repo()
    repo.item = None
    monkeypatch.setattr(link_stats, "get_repository", lambda: repo)
    event = {"pathParameters": {"code": "missing"}}
    response = link_stats.handler(event, SimpleNamespace())
    body = json.loads(response["body"])
    assert response["statusCode"] == 404
    assert body["error"]["code"] == "NOT_FOUND"
