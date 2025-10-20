from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from ..db.base import Base

class Activation(Base):
    __tablename__ = "activations"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False)
    machine_code = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    status = Column(Enum('active', 'deactivated', 'blacklisted', name='activation_status_enum'), default='active', nullable=False)
    activated_at = Column(DateTime, default=datetime.utcnow)
    deactivated_at = Column(DateTime, nullable=True)
    last_validated_at = Column(DateTime, nullable=True)
    blacklisted_at = Column(DateTime, nullable=True)
    
    # 硬體ID欄位（選填，支援硬體變化檢測）
    keypro_id = Column(String(255), nullable=True, index=True)
    motherboard_id = Column(String(255), nullable=True, index=True)
    disk_id = Column(String(255), nullable=True, index=True)

    license = relationship("License", back_populates="activations")