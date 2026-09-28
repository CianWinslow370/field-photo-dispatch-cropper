from fastapi import FastAPI, HTTPException

from .crop_client import InfraiCropClient, InfraiError
from .work_orders import DispatchUpdate, WorkOrderPhoto, prepare_dispatch

app = FastAPI(title="Field Photo Crop Service")


@app.post("/work-orders/crop", response_model=DispatchUpdate)
def crop_work_order_photo(photo: WorkOrderPhoto) -> DispatchUpdate:
    client = InfraiCropClient()
    try:
        return prepare_dispatch(photo, client)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    finally:
        client.close()

