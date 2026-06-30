
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class BackendInfo(BaseModel):
    id: str
    name: str
    description: str


class ProjectCreateRequest(BaseModel):
    name: str
    system_prompt: str | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    system_prompt: str | None = None


class FolderCreateRequest(BaseModel):
    path: str


class FolderResponse(BaseModel):
    id: int
    project_id: int
    path: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    system_prompt: str | None
    created_at: float
    folders: list[FolderResponse]


class ChatCreateRequest(BaseModel):
    project_id: int | None = None
    tool_backend: str | None = None


class ChatUpdateRequest(BaseModel):
    title: str | None = None


class ChatResponse(BaseModel):
    id: str
    project_id: int | None = None
    title: str = ""
    claude_session_id: str = ""
    tool_session_id: str | None = None
    tool_backend: str = "claude"
    created_at: float = 0.0
    updated_at: float = 0.0


class MessageResponse(BaseModel):
    id: int
    chat_id: str
    role: str = "user"
    content: str = ""
    tool_calls: list | None = None
    created_at: float = 0.0


class ChatSendRequest(BaseModel):
    chat_id: str
    message: str
