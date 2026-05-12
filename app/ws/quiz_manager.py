from enum import Enum
from typing import TYPE_CHECKING

from fastapi import WebSocket

if TYPE_CHECKING:
    from ..models.questions import Quiz


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


class QuizState(Enum):
    WAITING_FOR_PARTICIPANTS = "waiting_for_participants"
    IN_GAME = "in_game"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"


class QuizFlow:
    def __init__(self, quiz: Quiz, admin: WebSocket):
        self.admin = admin
        self.participants = ConnectionManager()
        self.state: QuizState = QuizState.WAITING_FOR_PARTICIPANTS
        self.quiz = quiz

    async def handle_admin_requests(self):
        pass

    async def handle_participants_requests(self):
        pass

    async def run(self):
        pass

    async def ban(self, user: WebSocket):
        pass

    async def interrupt(self):
        pass

    async def get_stats(self):
        pass


class NoParticipantsException(Exception): pass


class QuizWasInterrupted(Exception): pass


class ParticipantNotFound(Exception): pass
