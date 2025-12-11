from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- INPUT SCHEMAS (Dữ liệu gửi lên) ---

# Schema cơ bản cho License
class LicenseBase(BaseModel):
    key: str
    status: str = "active"
    plan: str = "Free"
    max_devices: int = 1
    expires_at: Optional[datetime] = None
    license_data: Optional[str] = None

# Dùng khi tạo mới (Create)
class LicenseCreate(LicenseBase):
    pass

# Dùng khi cập nhật (Update) - Tất cả field đều optional
class LicenseUpdate(BaseModel):
    key: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None
    max_devices: Optional[int] = None
    expires_at: Optional[datetime] = None
    license_data: Optional[str] = None

# --- OUTPUT SCHEMAS (Dữ liệu trả về) ---

# Schema hiển thị thông tin License (bao gồm ID và ngày tạo)
class LicenseRead(LicenseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Cho phép đọc từ SQLModel object

# Schema hiển thị thông tin Device
class DeviceRead(BaseModel):
    id: int
    hwid: str
    hostname: Optional[str]
    platform: Optional[str]
    last_seen_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Giữ lại các schema cũ của bạn
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