from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime

from app.database import get_session
from app.models import License, Device
from app.schemas import (
    LicenseCheckRequest, LicenseResponse, 
    LicenseCreate, LicenseRead, LicenseUpdate, 
    DeviceRead
)

router = APIRouter(prefix="/api/v1/license")

# =================================================================
# PUBLIC API (Client sử dụng để check key)
# =================================================================

@router.post("/check", response_model=LicenseResponse, tags=["Client"])
def check_license(data: LicenseCheckRequest, db: Session = Depends(get_session)):
    # 1. Tìm license
    lic = db.exec(select(License).where(License.key == data.key)).first()
    
    if not lic:
        return LicenseResponse(valid=False, message="Key không tồn tại")
    
    # 2. Kiểm tra trạng thái và hạn dùng
    if lic.status != "active":
        return LicenseResponse(valid=False, message="Key đã bị khóa")

    if lic.expires_at and lic.expires_at < datetime.utcnow():
        return LicenseResponse(valid=False, message="Key đã hết hạn")

    # 3. Kiểm tra thiết bị
    usage = db.exec(select(func.count(Device.id)).where(Device.license_id == lic.id)).one()

    current_device = db.exec(
        select(Device).where(Device.license_id == lic.id, Device.hwid == data.hwid)
    ).first()

    if current_device:
        # Update thông tin thiết bị cũ
        current_device.last_seen_at = datetime.utcnow()
        if data.hostname: current_device.hostname = data.hostname
        if data.platform: current_device.platform = data.platform
        db.add(current_device)
        db.commit()
    else:
        # Kiểm tra giới hạn thiết bị
        if usage >= lic.max_devices:
            return LicenseResponse(valid=False, message="Vượt quá số lượng máy cho phép")
        
        # Đăng ký thiết bị mới
        new_dev = Device(
            license_id=lic.id, 
            hwid=data.hwid, 
            hostname=data.hostname, 
            platform=data.platform
        )
        db.add(new_dev)
        db.commit()
        usage += 1

    return LicenseResponse(
        valid=True,
        message="Active",
        plan=lic.plan,
        expires_at=lic.expires_at,
        max_devices=lic.max_devices,
        used_devices=usage
    )

# 1. Xem danh sách License (Có phân trang)
@router.get("/", response_model=List[LicenseRead], tags=["Admin License"])
def read_licenses(
    offset: int = 0,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_session)
):
    licenses = db.exec(select(License).offset(offset).limit(limit)).all()
    return licenses

# 2. Tạo License mới
@router.post("/", response_model=LicenseRead, tags=["Admin License"])
def create_license(license_in: LicenseCreate, db: Session = Depends(get_session)):
    # Kiểm tra key trùng
    existing_key = db.exec(select(License).where(License.key == license_in.key)).first()
    if existing_key:
        raise HTTPException(status_code=400, detail="Key đã tồn tại")
    
    new_license = License.from_orm(license_in)
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return new_license

# 3. Xem chi tiết 1 License
@router.get("/{license_id}", response_model=LicenseRead, tags=["Admin License"])
def read_license_detail(license_id: int, db: Session = Depends(get_session)):
    lic = db.get(License, license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="License not found")
    return lic

# 4. Cập nhật License (Gia hạn, đổi plan, khóa key)
@router.patch("/{license_id}", response_model=LicenseRead, tags=["Admin License"])
def update_license(license_id: int, license_in: LicenseUpdate, db: Session = Depends(get_session)):
    lic = db.get(License, license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="License not found")

    update_data = license_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lic, key, value)
    
    lic.updated_at = datetime.utcnow()
    db.add(lic)
    db.commit()
    db.refresh(lic)
    return lic

# 5. Xóa License
@router.delete("/{license_id}", tags=["Admin License"])
def delete_license(license_id: int, db: Session = Depends(get_session)):
    lic = db.get(License, license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="License not found")
    
    devices = db.exec(select(Device).where(Device.license_id == license_id)).all()
    for dev in devices:
        db.delete(dev)
    
    db.delete(lic)
    db.commit()
    return {"ok": True, "message": "Deleted license and associated devices"}

# 6. Lấy danh sách người dùng (Devices) theo Key
@router.get("/by-key/{key}/devices", response_model=List[DeviceRead], tags=["Admin Devices"])
def get_devices_by_key(key: str, db: Session = Depends(get_session)):

    lic = db.exec(select(License).where(License.key == key)).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Key not found")
    
    devices = db.exec(select(Device).where(Device.license_id == lic.id)).all()
    return devices

@router.delete("/by-key/{key}/devices/{device_hwid}", tags=["Admin Devices"])
def delete_device_from_key(key: str, device_hwid: str, db: Session = Depends(get_session)):
    lic = db.exec(select(License).where(License.key == key)).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Key not found")
    
    device = db.exec(select(Device).where(Device.license_id == lic.id, Device.hwid == device_hwid)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device HWID not found for this key")
        
    db.delete(device)
    db.commit()
    return {"ok": True, "message": "Device removed from license"}