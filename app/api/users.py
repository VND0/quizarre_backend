from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt, verify_password, get_password_hash
from ..db.db import SessionDep
from ..models.user import User, UserPatch, PasswordChangeRequest

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
    responses={
        401: {"description": "JWT token is not given or expired or malformed"}
    }
)


@router.get("/me", response_model=User, )
def get_own_info(
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt)
):
    return session.exec(select(User).where(User.id == jwt_payload.sub)).one()


@router.patch(
    "/me",
    response_model=User,
    responses={
        409: {"description": "New email is busy"},
    }
)
def edit_user_info(
        session: SessionDep,
        update_data: UserPatch,
        jwt_payload: JwtPayload = Depends(verify_jwt)
):
    user = session.exec(select(User).where(User.id == jwt_payload.sub)).one()

    if update_data.email is not None and update_data.email != user.email:
        user_with_new_email = session.exec(select(User).where(User.email == update_data.email)).one_or_none()
        if user_with_new_email:
            raise HTTPException(409, "New email is busy")

    user.sqlmodel_update(update_data.model_dump(exclude_none=True))
    session.commit()
    session.refresh(user)
    return user


@router.patch(
    "/me/password",
    status_code=204,
    responses={
        403: {"description": "Old password is incorrect"},
        400: {"description": "New password is the same"}
    }
)
def change_password(
        session: SessionDep,
        request_data: PasswordChangeRequest,
        jwt_payload: JwtPayload = Depends(verify_jwt)
):
    if request_data.old_password == request_data.new_password:
        raise HTTPException(400)

    user = session.exec(select(User).where(User.id == jwt_payload.sub)).one()
    if not verify_password(request_data.old_password, user.password_hash):
        raise HTTPException(403)

    user.password_hash = get_password_hash(request_data.new_password)
    session.commit()


@router.delete("/me", response_model=User)
def delete_user(
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    user = session.exec(select(User).where(User.id == jwt_payload.sub)).one()
    user_dump = user.model_dump()
    password_hash = user.password_hash
    session.delete(user)
    session.commit()
    return User(
        **user_dump,
        password_hash=password_hash
    )
