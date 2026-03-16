from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Integer, Numeric, String, LargeBinary, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class BidCache(Base):
    __tablename__ = "bid_cache"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    context_hash = Column(String(64), nullable=False, unique=True)
    vertical = Column(String(32), nullable=False)
    encrypted_response = Column(LargeBinary, nullable=False)
    hit_count = Column(Integer, default=0)
    win_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_hit_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class BidHistory(Base):
    __tablename__ = "bid_history"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    bid_id = Column(UUID(as_uuid=True), nullable=False)
    context_hash = Column(String(64), nullable=False)
    vertical = Column(String(32), nullable=False)
    bid_amount = Column(Numeric(12, 6), nullable=False)
    w1 = Column(Numeric(6, 4), nullable=False, default=0.7)
    w2 = Column(Numeric(6, 4), nullable=False, default=0.3)
    won = Column(Boolean, nullable=False, default=False)
    payment_confirmed = Column(Boolean, nullable=False, default=False)
    revenue_credited = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Sponsor(Base):
    __tablename__ = "sponsors"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    vertical = Column(String(32), nullable=False)
    sponsor_name = Column(String(128), nullable=False)
    cta_type = Column(String(32), nullable=False)
    budget_remaining = Column(Numeric(14, 6), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
