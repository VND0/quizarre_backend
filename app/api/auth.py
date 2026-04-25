from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlmodel import select, Session

from ..core.config import REFRESH_TOKEN_EXPIRATION
from ..core.security import get_password_hash, create_refresh_token, create_access_token, get_refresh_token_hash, \
    verify_password
from ..db.db import SessionDep
from ..models.user import NewUser, User, UserResponse, OpaqueToken, LoginUser, ExistingRefreshToken, NewTokens

router = APIRouter(prefix="/api", tags=["Auth"])
refresh_token_issues_counter = 0

refresh_token_responses = {
    404: {"description": "Token not found"},
    401: {"description": "Token expired. You have to login with email and password again."}
}


def issue_refresh_token(user: User, session: Session, do_commit: bool = False):
    refresh_token = create_refresh_token()
    user.opaque_tokens.append(OpaqueToken(
        hash=get_refresh_token_hash(refresh_token),
        expiration=datetime.now() + REFRESH_TOKEN_EXPIRATION,
    ))
    if do_commit:
        session.commit()
    return refresh_token


def clear_expired_tokens(session: Session):
    global refresh_token_issues_counter

    refresh_token_issues_counter += 1
    if refresh_token_issues_counter % 500:
        return

    expired_tokens = session.exec(select(OpaqueToken).where(OpaqueToken.expiration < datetime.now())).all()
    for token in expired_tokens:
        session.delete(token)
    if expired_tokens:
        session.commit()


@router.post(
    "/register",
    response_model=UserResponse,
    responses={
        409: {"description": "User with this email already exists"}
    }
)
async def register(session: SessionDep, new_user: NewUser, background_tasks: BackgroundTasks):
    existing_user = session.exec(select(User).where(User.email == new_user.email)).one_or_none()
    if existing_user:
        raise HTTPException(409)

    password_hash = get_password_hash(new_user.password)
    user = User(
        **new_user.model_dump(),
        password_hash=password_hash
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    refresh_token = issue_refresh_token(user, session)
    access_token = create_access_token(user)
    session.commit()
    background_tasks.add_task(clear_expired_tokens, session)

    return UserResponse(
        user=User.model_validate(user),
        tokens=NewTokens(
            accessToken=access_token,
            refreshToken=refresh_token,
        )
    )


@router.post(
    "/login",
    response_model=UserResponse,
    responses={
        404: {"description": "Email or password is incorrect"}
    }
)
async def login(session: SessionDep, login_user: LoginUser, background_tasks: BackgroundTasks):
    user: User | None = session.exec(select(User).where(User.email == login_user.email)).one_or_none()
    if not (user and verify_password(login_user.password, user.password_hash)):
        raise HTTPException(404)

    refresh_token = issue_refresh_token(user, session)
    access_token = create_access_token(user)
    session.commit()
    background_tasks.add_task(clear_expired_tokens, session)
    return UserResponse(
        user=User.model_validate(user),
        tokens=NewTokens(
            accessToken=access_token,
            refreshToken=refresh_token,
        )
    )


@router.post(
    "/issue-refresh-token",
    response_model=NewTokens,
    responses=refresh_token_responses
)
def get_refresh_token(session: SessionDep, given_token: ExistingRefreshToken, background_tasks: BackgroundTasks):
    existing_token: OpaqueToken | None = session.exec(
        select(OpaqueToken).where(OpaqueToken.hash == get_refresh_token_hash(given_token.token))).one_or_none()

    if not existing_token:
        raise HTTPException(404)
    if existing_token.expiration < datetime.now():
        raise HTTPException(401)

    new_refresh_token = issue_refresh_token(existing_token.user, session, do_commit=True)
    new_access_token = create_access_token(existing_token.user)

    background_tasks.add_task(clear_expired_tokens, session)
    return NewTokens(
        accessToken=new_access_token,
        refreshToken=new_refresh_token,
    )


@router.post(
    "/issue-access-token",
    response_model=NewTokens,
    responses=refresh_token_responses
)
def get_access_token(session: SessionDep, refresh_token: ExistingRefreshToken):
    opaque_token: OpaqueToken | None = session.exec(
        select(OpaqueToken).where(OpaqueToken.hash == get_refresh_token_hash(refresh_token.token))).one_or_none()

    if not opaque_token:
        raise HTTPException(404)
    if opaque_token.expiration < datetime.now():
        raise HTTPException(401)

    return NewTokens(accessToken=create_access_token(opaque_token.user))
