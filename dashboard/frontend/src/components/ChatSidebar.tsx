import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { deleteJSON, getJSON, patchJSON, postJSON } from "../lib/api";
import { useConfirm } from "./ConfirmDialog";

export interface ProjectFolder {
  id: number;
  project_id: number;
  path: string;
  created_at: number;
}

export interface Project {
  id: number;
  name: string;
  system_prompt: string | null;
  created_at: number;
  folders: ProjectFolder[];
}

export interface ChatSummary {
  id: string;
  project_id: number | null;
  title: string;
  claude_session_id: string;
  created_at: number;
  updated_at: number;
}

interface ChatSidebarProps {
  activeChatId?: string;
  refreshKey: number;
}

export default function ChatSidebar({ activeChatId, refreshKey }: ChatSidebarProps) {
  const navigate = useNavigate();
  const { confirm, dialogElement } = useConfirm();
  const [projects, setProjects] = useState<Project[]>([]);
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [newProjectOpen, setNewProjectOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectPrompt, setNewProjectPrompt] = useState("");
  const [newFolderByProject, setNewFolderByProject] = useState<Record<number, string>>({});
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  function refresh() {
    Promise.all([getJSON<Project[]>("/api/projects"), getJSON<ChatSummary[]>("/api/chats")]).then(
      ([p, c]) => {
        setProjects(p);
        setChats(c);
      },
    );
  }

  useEffect(refresh, [refreshKey]);

  async function handleNewChat(projectId: number | null) {
    const chat = await postJSON<ChatSummary>("/api/chats", { project_id: projectId });
    navigate(`/chat/${chat.id}`);
    refresh();
  }

  async function handleCreateProject() {
    if (!newProjectName.trim()) return;
    await postJSON("/api/projects", {
      name: newProjectName.trim(),
      system_prompt: newProjectPrompt.trim() || null,
    });
    setNewProjectName("");
    setNewProjectPrompt("");
    setNewProjectOpen(false);
    refresh();
  }

  async function handleDeleteProject(id: number) {
    if (!(await confirm("¿Eliminar este proyecto? Los chats quedan sin proyecto."))) return;
    await deleteJSON(`/api/projects/${id}`);
    refresh();
  }

  async function handleAddFolder(projectId: number) {
    const path = (newFolderByProject[projectId] ?? "").trim();
    if (!path) return;
    try {
      await postJSON(`/api/projects/${projectId}/folders`, { path });
      setNewFolderByProject(prev => ({ ...prev, [projectId]: "" }));
      refresh();
    } catch (e) {
      alert((e as Error).message);
    }
  }

  async function handleRemoveFolder(folderId: number) {
    await deleteJSON(`/api/projects/folders/${folderId}`);
    refresh();
  }

  async function handleDeleteChat(id: string) {
    if (!(await confirm("¿Eliminar este chat?"))) return;
    await deleteJSON(`/api/chats/${id}`);
    if (id === activeChatId) navigate("/chat");
    refresh();
  }

  function startRename(chat: ChatSummary) {
    setRenamingId(chat.id);
    setRenameValue(chat.title || "Nuevo chat");
  }

  async function confirmRename(id: string) {
    const title = renameValue.trim();
    setRenamingId(null);
    if (!title) return;
    await patchJSON(`/api/chats/${id}`, { title });
    refresh();
  }

  const ungrouped = chats.filter(c => c.project_id === null);
  const byProject = (projectId: number) => chats.filter(c => c.project_id === projectId);

  return (
    <aside className="card chat-sidebar">
      <div className="card-title">Chats</div>
      <button className="btn btn-primary w-full mb-3" onClick={() => handleNewChat(null)}>
        + Nuevo chat
      </button>

      {projects.map(project => (
        <div key={project.id} className="chat-sidebar-project">
          <div className="chat-sidebar-project-header">
            <span>{project.name}</span>
            <div className="flex gap-1">
              <button
                className="chat-sidebar-icon-btn"
                onClick={() => handleNewChat(project.id)}
                title="Nuevo chat en este proyecto"
              >
                +
              </button>
              <button
                className="chat-sidebar-icon-btn"
                onClick={() => handleDeleteProject(project.id)}
                title="Eliminar proyecto"
              >
                ×
              </button>
            </div>
          </div>
          {project.folders.length > 0 && (
            <div className="chat-sidebar-folders">
              {project.folders.map(f => (
                <div key={f.id} className="chat-sidebar-folder">
                  <span>{f.path}</span>
                  <button className="chat-sidebar-icon-btn" onClick={() => handleRemoveFolder(f.id)}>
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="chat-sidebar-add-folder">
            <input
              className="input"
              placeholder="Agregar carpeta (path absoluto)..."
              value={newFolderByProject[project.id] ?? ""}
              onChange={e => setNewFolderByProject(prev => ({ ...prev, [project.id]: e.target.value }))}
              onKeyDown={e => {
                if (e.key === "Enter") handleAddFolder(project.id);
              }}
            />
          </div>
          <div className="file-list">
            {byProject(project.id).map(chat => (
              <ChatRow
                key={chat.id}
                chat={chat}
                active={chat.id === activeChatId}
                renaming={renamingId === chat.id}
                renameValue={renameValue}
                onSelect={() => navigate(`/chat/${chat.id}`)}
                onStartRename={() => startRename(chat)}
                onRenameChange={setRenameValue}
                onConfirmRename={() => confirmRename(chat.id)}
                onDelete={() => handleDeleteChat(chat.id)}
              />
            ))}
          </div>
        </div>
      ))}

      <div className="chat-sidebar-project-header">
        <span>Sin proyecto</span>
      </div>
      <div className="file-list mb-3">
        {ungrouped.map(chat => (
          <ChatRow
            key={chat.id}
            chat={chat}
            active={chat.id === activeChatId}
            renaming={renamingId === chat.id}
            renameValue={renameValue}
            onSelect={() => navigate(`/chat/${chat.id}`)}
            onStartRename={() => startRename(chat)}
            onRenameChange={setRenameValue}
            onConfirmRename={() => confirmRename(chat.id)}
            onDelete={() => handleDeleteChat(chat.id)}
          />
        ))}
      </div>

      {newProjectOpen ? (
        <div className="chat-sidebar-new-project">
          <input
            className="input mb-2"
            placeholder="Nombre del proyecto"
            value={newProjectName}
            onChange={e => setNewProjectName(e.target.value)}
          />
          <textarea
            className="input mb-2"
            placeholder="Instrucciones / contexto (opcional)"
            rows={3}
            value={newProjectPrompt}
            onChange={e => setNewProjectPrompt(e.target.value)}
          />
          <div className="flex gap-2">
            <button className="btn btn-primary" onClick={handleCreateProject}>
              Crear
            </button>
            <button className="btn btn-ghost" onClick={() => setNewProjectOpen(false)}>
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <button className="btn btn-ghost w-full" onClick={() => setNewProjectOpen(true)}>
          + Nuevo proyecto
        </button>
      )}
      {dialogElement}
    </aside>
  );
}

function ChatRow({
  chat,
  active,
  renaming,
  renameValue,
  onSelect,
  onStartRename,
  onRenameChange,
  onConfirmRename,
  onDelete,
}: {
  chat: ChatSummary;
  active: boolean;
  renaming: boolean;
  renameValue: string;
  onSelect: () => void;
  onStartRename: () => void;
  onRenameChange: (v: string) => void;
  onConfirmRename: () => void;
  onDelete: () => void;
}) {
  if (renaming) {
    return (
      <div className="file-item">
        <input
          className="input"
          autoFocus
          value={renameValue}
          onChange={e => onRenameChange(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter") onConfirmRename();
          }}
          onBlur={onConfirmRename}
        />
      </div>
    );
  }
  return (
    <div className={`file-item chat-sidebar-item ${active ? "active" : ""}`} onClick={onSelect}>
      <span className="chat-sidebar-title">{chat.title || "Nuevo chat"}</span>
      <div className="flex gap-1">
        <button
          className="chat-sidebar-icon-btn"
          onClick={e => {
            e.stopPropagation();
            onStartRename();
          }}
          title="Renombrar"
        >
          ✎
        </button>
        <button
          className="chat-sidebar-icon-btn"
          onClick={e => {
            e.stopPropagation();
            onDelete();
          }}
          title="Eliminar"
        >
          ×
        </button>
      </div>
    </div>
  );
}
