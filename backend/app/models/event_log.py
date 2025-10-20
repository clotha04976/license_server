from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from ..db.base import Base

class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=True)
    activation_id = Column(Integer, ForeignKey("activations.id"), nullable=True)
    event_type = Column(Enum('activation', 're_activation', 'hardware_change', 'validation', 'deactivation', name='event_type_enum'), nullable=False)
    event_subtype = Column(String(100), nullable=True)  # 如: 'machine_code_match', 'hardware_id_match', 'new_activation'
    serial_number = Column(String(255), nullable=False, index=True)
    machine_code = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # 儲存詳細資訊如硬體ID變化
    severity = Column(Enum('info', 'warning', 'suspicious', 'critical', name='severity_enum'), default='info')
    is_confirmed = Column(Boolean, default=False, nullable=False)  # 是否已確認
    confirmed_by = Column(String(255), nullable=True)  # 確認者
    confirmed_at = Column(DateTime, nullable=True)  # 確認時間
    created_at = Column(DateTime, default=datetime.utcnow)

    license = relationship("License")
    activation = relationship("Activation")
