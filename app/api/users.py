from fastapi import APIRouter, Depends
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..db.db import SessionDep
from ..models.user import User

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=User)
def get_own_info(
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt)
):
    return session.exec(select(User).where(User.id == jwt_payload.sub)).one()
