from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text

class License(SQLModel, table=True):
    __tablename__ = "license"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True, nullable=False, max_length=64)
    license: Optional[str] = Field(default=None, sa_column=Column(Text))
    plan: str = Field(default="Free", max_length=50)
    expires_at: Optional[datetime] = None
    max_version: Optional[str] = Field(default=None, max_length=50)
    max_devices: int = Field(default=1)
    status: str = Field(default="active", max_length=20)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    devices: List["Device"] = Relationship(back_populates="license", sa_relationship_kwargs={"cascade": "all, delete"})

class Device(SQLModel, table=True):
    __tablename__ = "device"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    license_id: int = Field(foreign_key="license.id", index=True)
    hwid: str = Field(index=True, max_length=64)
    hostname: Optional[str] = None
    platform: Optional[str] = None
    app_ver: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    license: Optional[License] = Relationship(back_populates="devices")