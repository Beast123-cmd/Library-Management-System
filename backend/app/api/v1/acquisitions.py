from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_admin, get_current_user
from app.db.database import get_db
from app.models.models import AcquisitionRequest, AcquisitionRequestStatus, AuditLog, User
from app.schemas.schemas import AcquisitionRequestCreate, AcquisitionRequestReview

router = APIRouter(prefix="/acquisitions", tags=["Acquisition requests"])


def serialize(request: AcquisitionRequest) -> dict:
    return {
        "id": request.id, "title": request.title, "author": request.author, "isbn": request.isbn,
        "reason": request.reason, "status": request.status.value, "staff_note": request.staff_note,
        "created_at": request.created_at, "reviewed_at": request.reviewed_at,
        "member": {"id": request.user.id, "name": request.user.name, "email": request.user.email} if request.user else None,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: AcquisitionRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = AcquisitionRequest(user_id=current_user.id, **payload.model_dump())
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return serialize(request)


@router.get("/")
async def list_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AcquisitionRequest).options(selectinload(AcquisitionRequest.user)).order_by(AcquisitionRequest.id.desc())
    if current_user.role.value != "admin":
        query = query.where(AcquisitionRequest.user_id == current_user.id)
    return [serialize(request) for request in (await db.execute(query)).scalars().all()]


@router.patch("/{request_id}")
async def review_request(
    request_id: int,
    payload: AcquisitionRequestReview,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    request = await db.get(AcquisitionRequest, request_id, with_for_update=True)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found.")
    if request.status != AcquisitionRequestStatus.pending:
        raise HTTPException(status_code=400, detail="This request has already been reviewed.")
    request.status = AcquisitionRequestStatus(payload.status)
    request.staff_note = payload.staff_note
    request.reviewed_at = datetime.now(timezone.utc)
    db.add(AuditLog(admin_id=admin.id, action="acquisition_request_reviewed", resource="acquisition_request", resource_id=request.id, details=f"status={payload.status}; note={payload.staff_note or ''}"))
    await db.commit()
    result = await db.execute(select(AcquisitionRequest).options(selectinload(AcquisitionRequest.user)).where(AcquisitionRequest.id == request.id))
    return serialize(result.scalar_one())
