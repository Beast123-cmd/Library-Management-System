import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Float,
    ForeignKey, Enum as SAEnum, Text, func
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class TransactionStatus(str, enum.Enum):
    requested = "requested"
    on_hold_shelf = "on_hold_shelf"
    in_transit = "in_transit"
    issued = "issued"
    returned = "returned"
    overdue = "overdue"
    lost = "lost"
# ==============================================================================
# USER MODEL
# ==============================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    username = Column(String(80), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole, native_enum=False), default=UserRole.member, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="admin")


# ==============================================================================
# BOOK MODEL
# ==============================================================================
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    author = Column(String(150), index=True, nullable=False)
    isbn = Column(String(20), unique=True, index=True, nullable=True)
    publish_year = Column(Integer, nullable=True)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    cover_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="book")


# ==============================================================================
# TRANSACTION MODEL
# ==============================================================================
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    issue_date = Column(Date, nullable=False)
    expected_return_date = Column(Date, nullable=False)
    actual_return_date = Column(Date, nullable=True)
    status = Column(SAEnum(TransactionStatus, native_enum=False), default=TransactionStatus.issued, index=True)
    fine_amount = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="transactions")
    book = relationship("Book", back_populates="transactions")


# ==============================================================================
# AUDIT LOG MODEL
# ==============================================================================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    admin = relationship("User", back_populates="audit_logs")


class HoldQueueStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


# ==============================================================================
# HOLD QUEUE MODEL
# ==============================================================================
class HoldQueue(Base):
    __tablename__ = "hold_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    request_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expiration_date = Column(DateTime(timezone=True), nullable=True) # E.g., hold shelf expires after 7 days
    status = Column(SAEnum(HoldQueueStatus, native_enum=False), default=HoldQueueStatus.active, index=True)
    
    # Relationships
    user = relationship("User")
    book = relationship("Book")
