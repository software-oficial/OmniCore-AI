import logging
from io import BytesIO
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("OmniCore.WhatsappApiGateway")


class WhatsappApiGateway:
    """
    Infrastructure Layer: Handles direct communication with the Meta WhatsApp Business API.
    Decouples the application logic from HTTP transport and API specifics.
    """

    def __init__(self, token: str, phone_id: str):
        self.token = token
        self.phone_id = phone_id
        self.base_url = "https://graph.facebook.com/v19.0"

    def _get_headers(
        self, content_type: Optional[str] = "application/json"
    ) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def send_text(self, to: str, body: str) -> Dict[str, Any]:
        if not self.token:
            raise ConnectionError("WhatsApp API Token not configured in environment")

        url = f"{self.base_url}/{self.phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }

        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        return response.json()

    def upload_media(self, filename: str, mime_type: str, file_content: bytes) -> str:
        if not self.token:
            raise ConnectionError("WhatsApp API Token not configured in environment")

        url = f"{self.base_url}/{self.phone_id}/media"
        files = {"file": (filename, BytesIO(file_content), mime_type)}
        data = {"messaging_product": "whatsapp"}

        response = requests.post(
            url, headers=self._get_headers(content_type=None), files=files, data=data
        )
        response.raise_for_status()
        return response.json().get("id")

    def send_media(
        self,
        to: str,
        media_id: str,
        media_type: str,
        caption: str = "",
        filename: str = "",
    ) -> Dict[str, Any]:
        if not self.token:
            raise ConnectionError("WhatsApp API Token not configured in environment")

        url = f"{self.base_url}/{self.phone_id}/messages"

        # Map internal media types to WhatsApp API types
        wapp_type = "document"
        if "image" in media_type:
            wapp_type = "image"
        elif "video" in media_type:
            wapp_type = "video"
        elif "audio" in media_type:
            wapp_type = "audio"

        payload_data: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": wapp_type,
            wapp_type: {"id": media_id},
        }
        if caption:
            payload_data[wapp_type]["caption"] = caption
        if wapp_type == "document" and filename:
            payload_data[wapp_type]["filename"] = filename

        response = requests.post(url, headers=self._get_headers(), json=payload_data)
        response.raise_for_status()
        return response.json()
