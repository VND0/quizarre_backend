import json
from enum import Enum
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket
from pydantic import BaseModel, ValidationError, Field

if TYPE_CHECKING:
    from ..models.questions import Quiz


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
        self._index_counter = -1

    @property
    def index_counter(self):
        self._index_counter += 1
        return self._index_counter

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        index = self.index_counter
        self.active_connections[index] = websocket
        return index

    def disconnect(self, target: int, code: int = 1000, reason: str | None = None):
        connection = self.active_connections.pop(target)
        connection.close(code, reason)

    async def send_personal_message(self, message: BaseModel, target: int):
        connection = self.active_connections[target]
        await connection.send_json(message.model_dump(by_alias=True, mode="json"))

    async def broadcast(self, message: BaseModel):
        message_content = message.model_dump(by_alias=True, mode="json")
        for connection in self.active_connections.values():
            await connection.send_json(message_content)


class AdminAction(Enum):
    RUN = "run"
    INTERRUPT = "interrupt"
    BAN = "ban"


class AdminRequest(BaseModel):
    action: AdminAction
    target: int | None


class WSResponse(BaseModel):
    type: WSResponseType
    error_code: int | None = Field(alias="errorCode", default=None)
    details: Any


class WSResponseType(Enum):
    ERROR = "error"
    SUCCESS = "success"
    MESSAGE = "message"


class QuizState(Enum):
    WAITING_FOR_PARTICIPANTS = "waiting_for_participants"
    IN_GAME = "in_game"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"


async def send_error(target: WebSocket, code: int, details: Any):
    data = WSResponse.model_validate({
        "type": "error",
        "errorCode": code,
        "details": details
    })
    await target.send_json(data.model_dump(by_alias=True, mode="json"))


class QuizFlow:
    def __init__(self, quiz: Quiz, admin: WebSocket):
        self.admin = admin
        self.participants = ConnectionManager()
        self.state: QuizState = QuizState.WAITING_FOR_PARTICIPANTS
        self.quiz = quiz

    async def handle_admin_requests(self):
        while True:
            if self.state in (QuizState.FINISHED, QuizState.INTERRUPTED):
                break
            try:
                text = await self.admin.receive_text()
                data = AdminRequest.model_validate(json.loads(text))
            except json.JSONDecodeError:
                await send_error(self.admin, 400, "Expected JSON, but got plain text")
                continue
            except ValidationError as e:
                await send_error(self.admin, 422, e.errors())
                continue

            if data.action == AdminAction.RUN:
                await self.run()
            elif data.action == AdminAction.BAN:
                await self.ban(data.target)
            elif data.action == AdminAction.INTERRUPT:
                await self.interrupt()

    async def run(self):
        pass

    async def ban(self, target: int | None):
        if target is None:
            await send_error(self.admin, 400, "Target not specified")
            return
        try:
            self.participants.disconnect(target)
        except KeyError:
            await send_error(self.admin, 400, "Target not found")
            return

        await self.admin.send_json(WSResponse.model_validate({
            "type": WSResponseType.SUCCESS,
            "details": target
        }).model_dump(by_alias=True, mode="json"))

    async def interrupt(self):
        pass

    async def get_admin_stats(self):
        pass

    async def handle_participants_requests(self):
        pass
