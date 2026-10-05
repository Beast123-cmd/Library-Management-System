from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ==============================================================================
# AUTH SCHEMAS
# ==============================================================================
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=80)
    password: Optional[str] = Field(None, min_length=6)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


# ==============================================================================
# USER SCHEMAS
# ==============================================================================
class UserOut(BaseModel):
    id: int
    name: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NotificationPreferences(BaseModel):
    due_reminders: bool
    overdue_alerts: bool
    hold_ready_alerts: bool


class NotificationPreferencesUpdate(BaseModel):
    due_reminders: Optional[bool] = None
    overdue_alerts: Optional[bool] = None
    hold_ready_alerts: Optional[bool] = None


# ==============================================================================
# BOOK SCHEMAS
# ==============================================================================
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=150)
    isbn: Optional[str] = None
    publish_year: Optional[int] = Field(None, ge=1000, le=2100)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    language: Optional[str] = Field(None, min_length=1, max_length=100)
    publisher: Optional[str] = Field(None, min_length=1, max_length=150)
    edition: Optional[str] = Field(None, min_length=1, max_length=100)
    shelf_location: Optional[str] = Field(None, min_length=1, max_length=100)
    total_copies: int = Field(1, ge=1)
    cover_url: Optional[str] = None
    description: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=150)
    isbn: Optional[str] = None
    publish_year: Optional[int] = Field(None, ge=1000, le=2100)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    language: Optional[str] = Field(None, min_length=1, max_length=100)
    publisher: Optional[str] = Field(None, min_length=1, max_length=150)
    edition: Optional[str] = Field(None, min_length=1, max_length=100)
    shelf_location: Optional[str] = Field(None, min_length=1, max_length=100)
    total_copies: Optional[int] = Field(None, ge=1)
    cover_url: Optional[str] = None
    description: Optional[str] = None


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    isbn: Optional[str] = None
    publish_year: Optional[int] = None
    category: Optional[str] = None
    language: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    shelf_location: Optional[str] = None
    total_copies: int
    available_copies: int
    cover_url: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BookCopyOut(BaseModel):
    id: int
    book_id: int
    copy_number: int
    accession_number: str
    status: str

    model_config = {"from_attributes": True}


# ==============================================================================
# TRANSACTION SCHEMAS
# ==============================================================================
class TransactionCreate(BaseModel):
    user_id: int
    book_id: int
    copy_id: Optional[int] = None
    expected_return_date: date

    @field_validator("expected_return_date")
    @classmethod
    def validate_return_window(cls, value: date) -> date:
        today = date.today()
        if value < today:
            raise ValueError("Return date cannot be in the past")
        if value > date.fromordinal(today.toordinal() + 90):
            raise ValueError("Return date must be within the next 90 days")
        return value


class ReturnRequest(BaseModel):
    waive_fine: bool = False
    waiver_reason: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def require_waiver_reason(self):
        if self.waive_fine and not (self.waiver_reason or "").strip():
            raise ValueError("A reason is required when waiving a fine.")
        self.waiver_reason = self.waiver_reason.strip() if self.waive_fine else None
        return self


class TransactionOut(BaseModel):
    id: int
    user_id: int
    book_id: int
    issue_date: date
    expected_return_date: date
    actual_return_date: Optional[date] = None
    status: str
    fine_amount: float
    renewal_count: int = 0
    user: Optional[UserOut] = None
    book: Optional[BookOut] = None
    copy_detail: Optional[BookCopyOut] = Field(None, validation_alias="copy", serialization_alias="copy")

    model_config = {"from_attributes": True}


class ReturnReceipt(TransactionOut):
    overdue_days: int
    assessed_fine: float
    waived: bool
    waiver_reason: Optional[str] = None


# ==============================================================================
# HOLD QUEUE SCHEMAS
# ==============================================================================
class HoldQueueOut(BaseModel):
    id: int
    user_id: int
    book_id: int
    request_date: datetime
    expiration_date: Optional[datetime] = None
    status: str
    user: Optional[UserOut] = None
    book: Optional[BookOut] = None

    model_config = {"from_attributes": True}

# ==============================================================================
# PAGINATION SCHEMA
# ==============================================================================
class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    data: list
