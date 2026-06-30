from fastapi import APIRouter, HTTPException, Request

from dashboard import chat_store
from dashboard.models.schemas import (
    FolderCreateRequest,
    FolderResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["projects"])


@router.get("/projects", response_model=list[ProjectResponse])
@limiter.limit("30/minute")
async def list_projects(request: Request):
    return await chat_store.list_projects()


@router.post("/projects", response_model=ProjectResponse)
@limiter.limit("10/minute")
async def create_project(request: Request, body: ProjectCreateRequest):
    project = await chat_store.create_project(body.name, body.system_prompt)
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
@limiter.limit("10/minute")
async def update_project(request: Request, project_id: int, body: ProjectUpdateRequest):
    project = await chat_store.update_project(project_id, body.name, body.system_prompt)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}")
@limiter.limit("10/minute")
async def delete_project(request: Request, project_id: int):
    ok = await chat_store.delete_project(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True}


@router.post("/projects/{project_id}/folders", response_model=FolderResponse)
@limiter.limit("10/minute")
async def create_folder(request: Request, project_id: int, body: FolderCreateRequest):
    folder = await chat_store.add_project_folder(project_id, body.path)
    return folder


@router.delete("/projects/folders/{folder_id}")
@limiter.limit("10/minute")
async def delete_folder(request: Request, folder_id: int):
    ok = await chat_store.remove_project_folder(folder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"ok": True}
