from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from dashboard.config import VAULT_DIR
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["notes"])


def _build_note_tree(path, prefix=""):
    entries = []
    try:
        for child in sorted(path.iterdir()):
            rel = child.name
            if child.is_dir():
                subtree = _build_note_tree(child, prefix + rel + "/")
                if subtree:
                    entries.append({"name": rel + "/", "type": "folder", "children": subtree})
            elif child.suffix == ".md":
                entries.append({"name": rel, "type": "file"})
    except PermissionError:
        return []
    return entries


@router.get("/notes/tree")
@limiter.limit("30/minute")
async def notes_tree(request: Request):
    if VAULT_DIR is None or not VAULT_DIR.exists():
        return []
    return _build_note_tree(VAULT_DIR)


@router.get("/notes/content")
@limiter.limit("30/minute")
async def note_content(request: Request, path: str = ""):
    if VAULT_DIR is None or not VAULT_DIR.exists():
        raise HTTPException(status_code=404, detail="Vault not found")
    full_path = VAULT_DIR / path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Note not found")
    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to read note {}: {}", path, exc)
        raise HTTPException(status_code=500, detail="Could not read note")
    return {"content": content, "path": path}
