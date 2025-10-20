from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta

from app.crud.base import CRUDBase
from app.models.event_log import EventLog
from app.schemas.event_log import EventLogCreate, EventLogUpdate


class CRUDEventLog(CRUDBase[EventLog, EventLogCreate, EventLogUpdate]):
    def get_unconfirmed_events_by_license_id(self, db: Session, *, license_id: int) -> List[EventLog]:
        """獲取指定授權的未確認事件"""
        return db.query(EventLog).filter(
            and_(
                EventLog.license_id == license_id,
                EventLog.is_confirmed == False
            )
        ).order_by(EventLog.created_at.desc()).all()

    def get_suspicious_events(self, db: Session, *, days: int = 7, limit: int = 100) -> List[EventLog]:
        """獲取可疑事件列表"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(EventLog).filter(
            and_(
                EventLog.severity.in_(['suspicious', 'critical']),
                EventLog.created_at >= cutoff_date
            )
        ).order_by(EventLog.created_at.desc()).limit(limit).all()

    def confirm_event(self, db: Session, *, event_id: int, confirmed_by: str) -> Optional[EventLog]:
        """確認事件"""
        event = db.query(EventLog).filter(EventLog.id == event_id).first()
        if event:
            event.is_confirmed = True
            event.confirmed_by = confirmed_by
            event.confirmed_at = datetime.utcnow()
            db.add(event)
            db.commit()
            db.refresh(event)
        return event

    def get_events_by_serial_number(self, db: Session, *, serial_number: str, limit: int = 50) -> List[EventLog]:
        """根據序號獲取事件列表"""
        return db.query(EventLog).filter(
            EventLog.serial_number == serial_number
        ).order_by(EventLog.created_at.desc()).limit(limit).all()

    def get_unconfirmed_count_by_license_id(self, db: Session, *, license_id: int) -> int:
        """獲取指定授權的未確認事件數量"""
        return db.query(EventLog).filter(
            and_(
                EventLog.license_id == license_id,
                EventLog.is_confirmed == False
            )
        ).count()


event_log = CRUDEventLog(EventLog)
