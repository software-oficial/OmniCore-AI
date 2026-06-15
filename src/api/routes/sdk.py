import os

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/sdk", tags=["SDK Distribution"])

SDK_PATH = "src/sdk/omnicore_sdk.py"


@router.get("/download")
async def download_sdk():
    """
    Provides the official OmniCore-AI Python SDK for local execution.
    Returns the omnicore_sdk.py file as a downloadable attachment.
    """
    if not os.path.exists(SDK_PATH):
        return Response(content="SDK file not found on server", status_code=404)

    return FileResponse(
        path=SDK_PATH, filename="omnicore_sdk.py", media_type="text/x-python"
    )
