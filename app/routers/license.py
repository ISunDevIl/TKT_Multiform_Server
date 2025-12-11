from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func
from typing import List
from datetime import datetime

from app.database import get_session
from app.models import License, Device
from app.schemas import (
    LicenseCheckRequest, LicenseResponse,
    LicenseCreate, LicenseRead, LicenseUpdate,
    DeviceRead
)

router = APIRouter(prefix="/api/v1/license", tags=["License Management"])

@router.post("/check", response_model=LicenseResponse, tags=["Client"])
def check_license(data: LicenseCheckRequest, db: Session = Depends(get_session)):
    # 1. Tìm license
    lic = db.exec(select(License).where(License.key == data.key)).first()
    
    if not lic:
        return LicenseResponse(valid=False, message="Key không tồn tại")
    
    # 2. Validate
    if lic.status != "active":
        return LicenseResponse(valid=False, message=f"Key bị khóa ({lic.status})")

    if lic.expires_at and lic.expires_at < datetime.utcnow():
        return LicenseResponse(valid=False, message="Key đã hết hạn sử dụng")
    
    # 3. Quản lý Device
    usage_count = db.exec(select(func.count(Device.id)).where(Device.license_id == lic.id)).one()

    current_device = db.exec(
        select(Device).where(Device.license_id == lic.id, Device.hwid == data.hwid)
    ).first()

    if current_device:
        current_device.last_seen_at = datetime.utcnow()
        if data.hostname: current_device.hostname = data.hostname
        if data.platform: current_device.platform = data.platform
        if data.app_ver: current_device.app_ver = data.app_ver
        
        db.add(current_device)
        db.commit()
    else:
        if usage_count >= lic.max_devices:
            return LicenseResponse(valid=False, message="Vượt quá số lượng thiết bị cho phép")
        
        new_dev = Device(
            license_id=lic.id,
            hwid=data.hwid,
            hostname=data.hostname,
            platform=data.platform,
            app_ver=data.app_ver
        )
        db.add(new_dev)
        db.commit()
        usage_count += 1

    return LicenseResponse(
        valid=True,
        message="Active",
        plan=lic.plan,
        expires_at=lic.expires_at,
        max_devices=lic.max_devices,
        used_devices=usage_count,
        license=lic.license
    )

@router.get("/", response_model=List[LicenseRead], tags=["Admin"])
def read_licenses(
    offset: int = 0,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_session)
):
    licenses = db.exec(select(License).offset(offset).limit(limit)).all()
    return licenses

@router.post("/", response_model=LicenseRead, tags=["Admin"], status_code=status.HTTP_201_CREATED)
def create_license(license_in: LicenseCreate, db: Session = Depends(get_session)):
    existing = db.exec(select(License).where(License.key == license_in.key)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Key đã tồn tại")
    
    new_license = License.from_orm(license_in)
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return new_license

@router.get("/{license_id}", response_model=LicenseRead, tags=["Admin"])
def read_license_detail(license_id: int, db: Session = Depends(get_session)):
    lic = db.get(License, license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="Không tìm thấy License")
    return lic

@router.patch("/{license_id}", response_model=LicenseRead, tags=["Admin"])
def update_license(license_id: int, license_in: LicenseUpdate, db: Session = Depends(get_session)):
    lic = db.get(License, license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="Không tìm thấy License")

    update_data = license_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lic, key, value)
    
    lic.updated_at = datetime.utcnow()
    db.add(lic)
    db.commit()
    db.refresh(lic)
    return lic

@router.delete("/{license_id}", tags=["Admin"])
def delete_license(license_id: int, db: Session = Depends(get_session)):
    lic = db.get(License, license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="Không tìm thấy License")
    
    devices = db.exec(select(Device).where(Device.license_id == license_id)).all()
    for dev in devices:
        db.delete(dev)
        
    db.delete(lic)
    db.commit()
    return {"message": "Đã xóa License và các thiết bị liên quan"}

@router.get("/by-key/{key}/devices", response_model=List[DeviceRead], tags=["Admin Devices"])
def get_devices_by_key(key: str, db: Session = Depends(get_session)):
    lic = db.exec(select(License).where(License.key == key)).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Key không tồn tại")
    return lic.devices

@router.delete("/by-key/{key}/devices/{device_hwid}", tags=["Admin Devices"])
def delete_device_from_key(key: str, device_hwid: str, db: Session = Depends(get_session)):
    lic = db.exec(select(License).where(License.key == key)).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Key không tồn tại")
    
    device = db.exec(select(Device).where(Device.license_id == lic.id, Device.hwid == device_hwid)).first()
    if not device:
        raise HTTPException(status_code=404, detail="HWID không tồn tại trong key này")
        
    db.delete(device)
    db.commit()
    return {"message": "Đã xóa thiết bị (Reset slot)"}