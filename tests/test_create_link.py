import json
import pathlib
import sys
from types import SimpleNamespace

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from handlers import create_link


class FakeRepo:
    def __init__(self):
        self.created = None
        self.counter = 100

    def next_counter(self):
        self.counter += 1
        return self.counter

    def create_link(self, **kwargs):
        self.created = kwargs
        return {
            "code": kwargs["code"],
            "destination": kwargs["destination"],
            "expiresAt": 123,
        }


def test_create_link_success(monkeypatch):
    repo = FakeRepo()
    monkeypatch.setattr(create_link, "get_repository", lambda: repo)

    event = {
        "body": json.dumps({"destination": "https://example.com"}),
    }
    response = create_link.handler(event, SimpleNamespace(aws_request_id="test"))
    body = json.loads(response["body"])
    assert response["statusCode"] == 201
    assert "shortUrl" in body
    assert repo.created["destination"] == "https://example.com"


def test_create_link_invalid_url(monkeypatch):
    monkeypatch.setattr(create_link, "get_repository", lambda: FakeRepo())
    event = {"body": json.dumps({"destination": "ftp://bad"})}
    response = create_link.handler(event, SimpleNamespace(aws_request_id="test"))
    body = json.loads(response["body"])
    assert response["statusCode"] == 400
    assert body["error"]["code"] == "INVALID_URL"
