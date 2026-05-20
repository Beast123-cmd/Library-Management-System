from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


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


# ==============================================================================
# BOOK SCHEMAS
# ==============================================================================
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=150)
    isbn: Optional[str] = None
    publish_year: Optional[int] = Field(None, ge=1000, le=2100)
    total_copies: int = Field(1, ge=1)
    cover_url: Optional[str] = None
    description: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=150)
    isbn: Optional[str] = None
    publish_year: Optional[int] = Field(None, ge=1000, le=2100)
    total_copies: Optional[int] = Field(None, ge=1)
    cover_url: Optional[str] = None
    description: Optional[str] = None


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    isbn: Optional[str] = None
    publish_year: Optional[int] = None
    total_copies: int
    available_copies: int
    cover_url: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==============================================================================
# TRANSACTION SCHEMAS
# ==============================================================================
class TransactionCreate(BaseModel):
    user_id: int
    book_id: int
    expected_return_date: date


class ReturnRequest(BaseModel):
    waive_fine: bool = False


class TransactionOut(BaseModel):
    id: int
    user_id: int
    book_id: int
    issue_date: date
    expected_return_date: date
    actual_return_date: Optional[date] = None
    status: str
    fine_amount: float
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
