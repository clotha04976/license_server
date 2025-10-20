from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from ..db.base import Base

class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    serial_number = Column(String(255), unique=True, index=True, nullable=False)
    features = Column(JSON, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    max_activations = Column(Integer, default=1)
    status = Column(Enum('pending', 'active', 'expired', 'disabled', name='license_status_enum'), default='pending', nullable=False)
    connection_type = Column(Enum('network', 'standalone', name='license_connection_type_enum'), default='network', nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="licenses")
    product = relationship("Product", back_populates="licenses")
    activations = relationship("Activation", back_populates="license", cascade="all, delete-orphan")