import httpx

from field_crop_service.crop_client import InfraiCropClient


def test_smart_crop_retries_rate_limit_and_keeps_request_key() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "0"},
                json={"ok": False, "data": None, "error": {"code": "RATE_LIMITED"}, "metadata": {}},
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"asset": "crop-4x3"}, "error": None, "metadata": {}},
        )

    client = InfraiCropClient(
        "test-key",
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    image = {"base64": "aW1hZ2UtYnl0ZXM="}
    result = client.smart_crop(image, "4:3", "crop-WO-1")
    client.close()

    assert result == {"asset": "crop-4x3"}
    assert len(requests) == 2
    assert all(request.content == b'{"image":{"base64":"aW1hZ2UtYnl0ZXM="},"aspect":"4:3"}' for request in requests)
    assert {request.headers["Idempotency-Key"] for request in requests} == {"crop-WO-1"}
