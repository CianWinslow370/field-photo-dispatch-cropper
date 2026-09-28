from field_crop_service.work_orders import WorkOrderPhoto, prepare_dispatch


class RecordingCropper:
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, str], str, str]] = []

    def smart_crop(self, image: dict[str, str], aspect: str, request_key: str) -> dict:
        self.calls.append((image, aspect, request_key))
        return {"asset": f"crop-{aspect}"}


def test_completed_variants_make_work_order_dispatchable_and_flag_follow_up() -> None:
    cropper = RecordingCropper()
    photo = WorkOrderPhoto(
        work_order_id="WO-1842",
        image={"base64": "aW1hZ2UtYnl0ZXM="},
        aspects=["4:3", "1:1", "4:3"],
        technician_note="Check the seal on the return visit.",
    )

    update = prepare_dispatch(photo, cropper)

    assert update.dispatch_status == "ready_for_dispatch"
    assert update.follow_up_required is True
    assert [variant.aspect for variant in update.variants] == ["4:3", "1:1"]
    assert cropper.calls == [
        (
            photo.image,
            "4:3",
            "work-order:WO-1842:crop:4:3",
        ),
        (
            photo.image,
            "1:1",
            "work-order:WO-1842:crop:1:1",
        ),
    ]
