import httpx

from strategies.filesystem.client import DatasetMetadataClient


def _mount_transport(client: DatasetMetadataClient, handler):
    client._transport = httpx.MockTransport(handler)  # test hook (Task 6 Step 3)


def test_get_returns_name_and_description():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "d1", "name": "HR", "description": "HR docs"},
                    {"id": "d2", "name": "KB", "description": ""},
                ],
                "has_more": False,
            },
        )

    c = DatasetMetadataClient("http://x/v1", "key")
    _mount_transport(c, handler)
    assert c.get("d1") == {"name": "HR", "description": "HR docs"}
    assert c.get("d2") == {"name": "KB", "description": ""}


def test_get_falls_back_when_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [], "has_more": False})

    c = DatasetMetadataClient("http://x/v1", "key")
    _mount_transport(c, handler)
    assert c.get("unknown") == {"name": "unknown", "description": ""}


def test_get_falls_back_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    c = DatasetMetadataClient("http://x/v1", "key")
    _mount_transport(c, handler)
    assert c.get("d1") == {"name": "d1", "description": ""}
