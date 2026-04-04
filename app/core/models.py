from pydantic import BaseModel
from uuid import UUID


class JwtPayload(BaseModel):
    sub: UUID
