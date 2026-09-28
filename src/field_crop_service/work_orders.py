from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class Cropper(Protocol):
    def smart_crop(self, image: dict[str, str], aspect: str, request_key: str) -> dict:
        raise AssertionError("Protocol method called directly")


class WorkOrderPhoto(BaseModel):
    work_order_id: str = Field(min_length=1)
    image: dict[str, str]
    aspects: list[str] = Field(min_length=1)
    technician_note: str | None = None


class CropVariant(BaseModel):
    aspect: str
    result: dict


class DispatchUpdate(BaseModel):
    work_order_id: str
    dispatch_status: str
    follow_up_required: bool
    variants: list[CropVariant]


def prepare_dispatch(photo: WorkOrderPhoto, cropper: Cropper) -> DispatchUpdate:
    unique_aspects = list(dict.fromkeys(photo.aspects))
    variants = [
        CropVariant(
            aspect=aspect,
            result=cropper.smart_crop(
                photo.image,
                aspect,
                f"work-order:{photo.work_order_id}:crop:{aspect}",
            ),
        )
        for aspect in unique_aspects
    ]
    return DispatchUpdate(
        work_order_id=photo.work_order_id,
        dispatch_status="ready_for_dispatch",
        follow_up_required=bool(photo.technician_note),
        variants=variants,
    )
