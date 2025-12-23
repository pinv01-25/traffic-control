from typing import Literal

from pydantic import BaseModel


class DownloadRequest(BaseModel):
    traffic_light_id: str
    timestamp: str
    type: Literal["data", "optimization"]