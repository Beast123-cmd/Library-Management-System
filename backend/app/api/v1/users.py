from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.db.database import get_db
from app.core.security import get_password_hash
from app.schemas.schemas import UserOut, PaginatedResponse, UserCreate, UserUpdate
from app.models.models import User, UserRole, Transaction, TransactionStatus
from app.core.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/users", tags=["Users & Members"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current logged-in user's profile."""
    return current_user


@router.get("/", response_model=PaginatedResponse)
async def list_members(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """List all members. Admin only."""
    query = select(User).where(User.role == UserRole.member)
    count_query = select(func.count()).select_from(User).where(User.role == UserRole.member)

    if search:
        search_filter = User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%") | User.username.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page).order_by(User.name))
    members = result.scalars().all()

    return PaginatedResponse(
        total=total, page=page, per_page=per_page,
        data=[UserOut.model_validate(m) for m in members]
    )


@router.post("/", response_model=UserOut, status_code=201)
async def create_member(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Create a new member account. Admin only."""
    result = await db.execute(
        select(User).where((User.email == payload.email) | (User.username == payload.username))
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="A user with this email or username already exists."
        )

    new_user = User(
        name=payload.name,
        email=payload.email,
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.member
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.put("/{user_id}", response_model=UserOut)
async def update_member(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Update a member account. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.name is not None:
        user.name = payload.name
    if payload.email is not None:
        # Check email uniqueness
        email_check = await db.execute(select(User).where(User.email == payload.email, User.id != user_id))
        if email_check.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email is already taken.")
        user.email = payload.email
    if payload.username is not None:
        # Check username uniqueness
        username_check = await db.execute(select(User).where(User.username == payload.username, User.id != user_id))
        if username_check.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username is already taken.")
        user.username = payload.username
    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_member(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Delete a member permanently. Block if they have active loans. Admin only."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Check for active loans
    txn_check = await db.execute(
        select(Transaction).where(Transaction.user_id == user_id, Transaction.status == TransactionStatus.issued)
    )
    if txn_check.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user. Member has active, unreturned books."
        )

    await db.delete(user)
    await db.commit()


@router.patch("/{user_id}/toggle-active", response_model=UserOut)
async def toggle_member_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Toggle a member's active status. Admin only."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot change your own status.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)
    return user


