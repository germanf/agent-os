import { useEffect, useState } from "react";
import { getJSON, postJSON } from "../lib/api";

interface MCPServer {
  name: string;
  version: string;
  tool_count: number;
  resource_count: number;
}

interface MCPTool {
  server: string;
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

interface MCPResource {
  server: string;
  uri: string;
  name: string;
  description: string;
  mime_type: string;
}

interface CallResult {
  result: unknown;
}

export default function McpAdmin() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [resources, setResources] = useState<MCPResource[]>([]);
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [serverTools, setServerTools] = useState<MCPTool[]>([]);
  const [serverResources, setServerResources] = useState<MCPResource[]>([]);
  const [callTool, setCallTool] = useState("");
  const [callArgs, setCallArgs] = useState("{}");
  const [callResult, setCallResult] = useState("");
  const [callError, setCallError] = useState("");

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    const [s, t] = await Promise.all([
      getJSON<MCPServer[]>("/api/mcp/servers").catch(() => []),
      getJSON<MCPTool[]>("/api/mcp/tools").catch(() => []),
    ]);
    setServers(s);
    setTools(t);
    setResources([]);
  }

  async function selectServer(name: string) {
    setSelectedServer(name);
    setCallResult("");
    setCallError("");
    const [toolsRes, resourcesRes] = await Promise.all([
      getJSON<MCPTool[]>(`/api/mcp/servers/${name}/tools`).catch(() => []),
      getJSON<MCPResource[]>(`/api/mcp/servers/${name}/resources`).catch(() => []),
    ]);
    setServerTools(toolsRes);
    setServerResources(resourcesRes);
  }

  async function handleCall(serverName: string) {
    setCallResult("");
    setCallError("");
    try {
      const args = JSON.parse(callArgs);
      const result = await postJSON<CallResult>(`/api/mcp/servers/${serverName}/call`, {
        tool: callTool,
        args,
      });
      setCallResult(JSON.stringify(result?.result ?? result, null, 2));
    } catch (e) {
      setCallError(String(e));
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">MCP Admin</h2>

      <div className="card p-4">
        <h3 className="font-semibold mb-3">Servers ({servers.length})</h3>
        <div className="flex flex-wrap gap-3">
          {servers.map(s => (
            <button
              key={s.name}
              className={`px-3 py-2 rounded text-sm border ${selectedServer === s.name ? "border-accent bg-accent/10" : "border-border"}`}
              onClick={() => selectServer(s.name)}
            >
              <span className="font-medium">{s.name}</span>
              <span className="text-xs text-text-muted ml-2">v{s.version}</span>
              <span className="text-xs text-text-muted ml-2">{s.tool_count} tools</span>
            </button>
          ))}
          {servers.length === 0 && <p className="text-text-muted text-sm">No MCP servers registered</p>}
        </div>
        <button className="btn-ghost text-xs mt-2" onClick={loadAll}>Refresh</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-4">
          <h3 className="font-semibold mb-2">All Tools ({tools.length})</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {tools.map((t, i) => (
              <details key={i} className="border border-border rounded p-2">
                <summary className="text-sm cursor-pointer">
                  <span className="text-accent">{t.server}</span>
                  <span className="ml-2 font-medium">{t.name}</span>
                </summary>
                <p className="text-xs text-text-muted mt-1">{t.description}</p>
                <pre className="text-xs bg-bg p-2 rounded mt-1 overflow-x-auto">{JSON.stringify(t.input_schema, null, 2)}</pre>
              </details>
            ))}
          </div>
        </div>

        <div className="card p-4">
          <h3 className="font-semibold mb-2">Resources ({resources.length})</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {resources.map((r, i) => (
              <div key={i} className="border border-border rounded p-2 text-sm">
                <span className="text-accent">{r.server}</span>
                <span className="ml-2 font-medium">{r.name}</span>
                <p className="text-xs text-text-muted mt-1">{r.uri}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedServer && (
        <div className="card p-4 space-y-4">
          <h3 className="font-semibold">Server: {selectedServer}</h3>

          <div>
            <h4 className="text-sm font-medium mb-2">Tools</h4>
            <div className="space-y-2">
              {serverTools.map((t, i) => (
                <div key={i} className="border border-border rounded p-2 text-sm flex items-center gap-2">
                  <span className="font-medium">{t.name}</span>
                  <span className="text-xs text-text-muted flex-1">{t.description}</span>
                  <button
                    className="btn-ghost text-xs"
                    onClick={() => { setCallTool(t.name); setCallArgs(JSON.stringify(t.input_schema?.properties ? Object.fromEntries(Object.keys(t.input_schema.properties).map(k => [k, ""])) : {}, null, 2)); }}
                  >
                    Test
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-border rounded p-3 space-y-2">
            <h4 className="text-sm font-medium">Test Tool</h4>
            {callTool && (
              <>
                <p className="text-xs">Tool: <span className="text-accent">{callTool}</span></p>
                <textarea
                  className="input w-full h-24 font-mono text-xs"
                  value={callArgs}
                  onChange={e => setCallArgs(e.target.value)}
                />
                <button className="btn-primary text-xs" onClick={() => handleCall(selectedServer)}>Call</button>
              </>
            )}
            {callResult && <pre className="text-xs bg-bg p-2 rounded max-h-40 overflow-y-auto">{callResult}</pre>}
            {callError && <p className="text-xs text-red-400">{callError}</p>}
          </div>

          <div>
            <h4 className="text-sm font-medium mb-2">Resources</h4>
            <div className="space-y-1">
              {serverResources.map((r, i) => (
                <div key={i} className="text-xs text-text-muted">
                  <span className="text-accent">{r.uri}</span>
                  <span className="ml-2">{r.name}</span>
                </div>
              ))}
              {serverResources.length === 0 && <p className="text-xs text-text-muted">No resources</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
