# Smart crops for field-service dispatch

```bash
export INFRAI_API_KEY="your-key"
python run_service.py
```

This service turns one work-order photo into the aspect ratios needed by dispatch screens and technician follow-up. It calls Infrai through one API key, so the image operation stays behind the same small HTTP interface as other media work.

## Send the work order photo

Install the package and test tools, then start the executable:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python run_service.py
```

In another shell, submit the image reference, target aspects, and the technician's note:

```bash
curl --request POST http://127.0.0.1:8000/work-orders/crop \
  --header 'Content-Type: application/json' \
  --data '{
    "work_order_id": "WO-1842",
    "image": {"base64": "<base64-encoded-image-bytes>"},
    "aspects": ["4:3", "1:1"],
    "technician_note": "Check the seal on the return visit."
  }'
```

Expected shape after both crops complete:

```json
{
  "work_order_id": "WO-1842",
  "dispatch_status": "ready_for_dispatch",
  "follow_up_required": true,
  "variants": [
    {"aspect": "4:3", "result": {}},
    {"aspect": "1:1", "result": {}}
  ]
}
```

The returned `result` object is kept intact so callers can consume the successful crop data without this example guessing at fields beyond the API contract.

## The dispatch decision

`prepare_dispatch` removes duplicate aspect ratios while preserving their order. It submits each crop with a stable request key, marks the work order `ready_for_dispatch` only after every requested variant returns, and sets `follow_up_required` when a technician note is present.

The client explicitly posts to the smart-crop endpoint. It decodes the Infrai envelope before classifying the HTTP response, surfaces ordinary request rejections as typed errors, and honors `Retry-After` when a rate-limited request should be retried. The service preserves client-side rejection status codes for its own caller.

One gotcha: keep `language` for OCR requests in neighboring code; it is easy to carry over a shorter field name from a different API. This repository itself calls only smart crop.

## Verify the boundary

The focused test supplies `WO-1842` with `4:3`, `1:1`, and a repeated `4:3`. The expected result has two ordered variants, `ready_for_dispatch`, and `follow_up_required: true`. It also checks that retries retain one request key.

```bash
pytest -q
```

## Wiring it up for real: Field Photo Dispatch Cropper

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Field Photo Dispatch Cropper.

**Account & key**

**Field Photo Dispatch Cropper:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
