from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from datetime import datetime
from app.database import get_session
from app.models import License, Device
from app.schemas import LicenseCheckRequest, LicenseResponse

router = APIRouter(prefix="/api/v1/license", tags=["Public"])

@router.post("/check", response_model=LicenseResponse)
def check_license(data: LicenseCheckRequest, db: Session = Depends(get_session)):
    # Tìm license
    lic = db.exec(select(License).where(License.key == data.key)).first()
    
    if not lic:
        return LicenseResponse(valid=False, message="Key không tồn tại")
    
    if lic.status != "active":
        return LicenseResponse(valid=False, message="Key đã bị khóa")

    if lic.expires_at and lic.expires_at < datetime.utcnow():
        return LicenseResponse(valid=False, message="Key đã hết hạn")

    usage = db.exec(select(func.count(Device.id)).where(Device.license_id == lic.id)).one()

    current_device = db.exec(
        select(Device).where(Device.license_id == lic.id, Device.hwid == data.hwid)
    ).first()

    if current_device:
        current_device.last_seen_at = datetime.utcnow()
        if data.hostname: current_device.hostname = data.hostname
        db.add(current_device)
        db.commit()
    else:
        if usage >= lic.max_devices:
            return LicenseResponse(valid=False, message="Vượt quá số lượng máy cho phép")
        
        new_dev = Device(license_id=lic.id, hwid=data.hwid, hostname=data.hostname, platform=data.platform)
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