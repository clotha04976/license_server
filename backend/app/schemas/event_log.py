from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class EventLogBase(BaseModel):
    event_type: str
    event_subtype: Optional[str] = None
    serial_number: str
    machine_code: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    severity: str = 'info'
    is_confirmed: bool = False
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None


class EventLogCreate(EventLogBase):
    license_id: Optional[int] = None
    activation_id: Optional[int] = None


class EventLogUpdate(BaseModel):
    is_confirmed: Optional[bool] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None


class EventLog(EventLogBase):
    id: int
    license_id: Optional[int] = None
    activation_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EventConfirmationRequest(BaseModel):
    event_id: int
    confirmed_by: str
