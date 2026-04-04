from fastapi import APIRouter
from ..models.user import NewUser

router = APIRouter(prefix="/api", tags=["Auth"])


@router.post("/register")
async def register(new_user: NewUser):
    pass


@router.post("/login")
async def login():
    pass

