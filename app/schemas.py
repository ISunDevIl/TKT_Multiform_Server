from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LicenseBase(BaseModel):
    key: str
    license: Optional[str] = None
    plan: str = "Free"
    max_devices: int = 1
    max_version: Optional[str] = None
    status: str = "active"
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

class LicenseCreate(LicenseBase):
    pass

class LicenseUpdate(BaseModel):
    license: Optional[str] = None
    plan: Optional[str] = None
    max_devices: Optional[int] = None
    max_version: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

class DeviceRead(BaseModel):
    id: int
    hwid: str
    hostname: Optional[str]
    platform: Optional[str]
    app_ver: Optional[str]
    last_seen_at: datetime
    created_at: datetime

class LicenseRead(LicenseBase):
    id: int
    created_at: datetime
    updated_at: datetime

class LicenseCheckRequest(BaseModel):
    key: str
    hwid: str
    hostname: Optional[str] = None
    platform: Optional[str] = None
    app_ver: Optional[str] = None
class LicenseResponse(BaseModel):
    valid: bool
    message: str
    plan: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_devices: int = 0
    used_devices: int = 0
    license: Optional[str] = None