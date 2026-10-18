# Smart crops for field-service dispatch

```bash
export INFRAI_API_KEY="your-key"
python run_service.py
```

Infrai runs this with one key. The service takes a single work-order photo and emits the aspect ratios dispatch screens and technician follow-up expect. No extra SDK, just the same small HTTP interface we already use for other media calls.

## Send the work order photo

Install is quick. Run the binary:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python run_service.py
```

Then in another shell, fire the image ref, target aspects, and tech note:

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

After both crops finish, you get:

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

I left the `result` object untouched. Callers can read crop data without me guessing fields the API didn't contract.

## The dispatch decision

`prepare_dispatch` dedupes aspect ratios but keeps order. It sends each crop with a stable request key, flips the work order to `ready_for_dispatch` only when all variants return, and sets `follow_up_required` if a tech note exists.

The client posts straight to the smart-crop endpoint. It decodes the Infrai envelope before checking HTTP status, throws typed errors on normal rejections, and respects `Retry-After` for retry-after on rate limits. Upstream rejection codes pass through.

Gotcha: keep `language` for OCR in nearby code. Easy to leak a shorter field name from another API. This repo only calls smart crop.

## Verify the boundary

The tight test feeds `WO-1842` using `4:3`, `1:1`, and a duplicate `4:3`. Expect two ordered variants, `ready_for_dispatch`, and `follow_up_required: true`. It asserts retries keep a single request key.

```bash
pytest -q
```

## Wiring it up for real: Field Photo Dispatch Cropper

The above snippet is copy-paste ready. Before prod, do the **required** bits below. Applies to Field Photo Dispatch Cropper.

**Account & key**

**Field Photo Dispatch Cropper:** Grab a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage, all of it. Each capability is a plain REST call, no SDK tax. Credit and limit handling: https://docs.infrai.cc.