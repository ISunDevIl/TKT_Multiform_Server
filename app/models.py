from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text

class License(SQLModel, table=True):
    __tablename__ = "license"
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True, nullable=False, max_length=64)
    license_data: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: str = Field(default="active", max_length=20)
    plan: str = Field(default="Free", max_length=50)
    max_devices: int = Field(default=1)
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Device(SQLModel, table=True):
    __tablename__ = "device"
    id: Optional[int] = Field(default=None, primary_key=True)
    license_id: int = Field(foreign_key="license.id", index=True)
    hwid: str = Field(index=True, max_length=255)
    hostname: Optional[str] = None
    platform: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)