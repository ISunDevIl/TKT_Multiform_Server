from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LicenseCheckRequest(BaseModel):
    key: str
    hwid: str
    hostname: Optional[str] = None
    platform: Optional[str] = None

class LicenseResponse(BaseModel):
    valid: bool
    message: str
    plan: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_devices: int = 0
    used_devices: int = 0