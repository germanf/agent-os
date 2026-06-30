import { useEffect, useRef, useState } from "react";
import { getJSON } from "../lib/api";
import { parseAndSanitize, sanitizeHtml } from "../lib/sanitize";

interface NoteNode {
  name: string;
  path: string;
  type: "file" | "dir";
  children?: NoteNode[];
}

export default function Notes() {
  const [tree, setTree] = useState<NoteNode[] | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [html, setHtml] = useState<string | null>(null);
  const [loadingContent, setLoadingContent] = useState(false);
  const [error, setError] = useState(false);

  const byPath = useRef(new Map<string, NoteNode>());
  const byBasename = useRef(new Map<string, NoteNode>());

  useEffect(() => {
    getJSON<NoteNode[]>("/api/notes/tree")
      .then(t => {
        indexTree(t, byPath.current, byBasename.current);
        setTree(t);
      })
      .catch(() => setTree([]));
  }, []);

  async function openNote(path: string) {
    setSelectedPath(path);
    setLoadingContent(true);
    setError(false);
    try {
      const { content } = await getJSON<{ path: string; content: string }>(
        `/api/notes/content?path=${encodeURIComponent(path)}`,
      );
      const resolved = resolveWikilinks(content, byPath.current, byBasename.current);
      const sanitized = sanitizeHtml(await parseAndSanitize(resolved));
      setHtml(sanitized);
    } catch {
      setError(true);
    } finally {
      setLoadingContent(false);
    }
  }

  function handleContentClick(e: React.MouseEvent<HTMLDivElement>) {
    const link = (e.target as HTMLElement).closest<HTMLAnchorElement>("a.wikilink");
    if (!link) return;
    e.preventDefault();
    const target = link.dataset.target;
    if (target) openNote(target);
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-4 items-start">
      <aside className="card">
        <div className="card-title">Vault</div>
        {tree === null ? (
          <p className="text-text-muted text-[13px]">Cargando...</p>
        ) : tree.length === 0 ? (
          <p className="text-text-muted text-[13px]">Vault no disponible en este entorno.</p>
        ) : (
          <div className="file-list">
            <NoteTree nodes={tree} onSelect={openNote} />
          </div>
        )}
      </aside>
      <section className="card notes-content">
        {selectedPath === null && <p className="text-text-muted text-[13px]">Seleccioná una nota.</p>}
        {selectedPath !== null && loadingContent && (
          <p className="text-text-muted text-[13px]">Cargando...</p>
        )}
        {selectedPath !== null && !loadingContent && error && (
          <p className="text-danger text-[13px]">No se pudo cargar la nota.</p>
        )}
        {selectedPath !== null && !loadingContent && !error && html !== null && (
          <div onClick={handleContentClick} dangerouslySetInnerHTML={{ __html: html }} />
        )}
      </section>
    </div>
  );
}

function NoteTree({
  nodes,
  depth = 0,
  onSelect,
}: {
  nodes: NoteNode[];
  depth?: number;
  onSelect: (path: string) => void;
}) {
  return (
    <>
      {nodes.map(node =>
        node.type === "dir" ? (
          <div key={node.path || node.name}>
            <div className="text-text-muted text-xs mt-1" style={{ marginLeft: depth * 12 }}>
              📁 {node.name}
            </div>
            <NoteTree nodes={node.children ?? []} depth={depth + 1} onSelect={onSelect} />
          </div>
        ) : (
          <div
            key={node.path}
            className="file-item cursor-pointer"
            style={{ marginLeft: depth * 12 }}
            onClick={() => onSelect(node.path)}
          >
            <span className="file-name">📄 {node.name}</span>
          </div>
        ),
      )}
    </>
  );
}

function indexTree(nodes: NoteNode[], byPath: Map<string, NoteNode>, byBasename: Map<string, NoteNode>) {
  for (const node of nodes) {
    if (node.type === "file") {
      byPath.set(node.path, node);
      byBasename.set(node.name, node);
    } else if (node.children) {
      indexTree(node.children, byPath, byBasename);
    }
  }
}

function resolveWikilinks(
  raw: string,
  byPath: Map<string, NoteNode>,
  byBasename: Map<string, NoteNode>,
): string {
  return raw.replace(/\[\[([^\]|]+)(\|([^\]]+))?\]\]/g, (_match, target: string, _pipe, alias?: string) => {
    const label = alias || target;
    const note =
      byPath.get(target) ?? byPath.get(target + ".md") ?? byBasename.get(target) ?? byBasename.get(target + ".md");
    if (!note) return `<span class="wikilink wikilink-missing">${label}</span>`;
    return `<a class="wikilink" href="#" data-target="${note.path}">${label}</a>`;
  });
}
