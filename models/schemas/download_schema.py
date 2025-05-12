from pydantic import BaseModel
from typing import Literal

class DownloadRequest(BaseModel):
    traffic_light_id: str
    timestamp: str
    type: Literal["data", "optimization"]