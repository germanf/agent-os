import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getJSON, postJSON } from "../lib/api";
import { uuid } from "../lib/uuid";
import {
  isSpeechRecognitionSupported,
  isSpeechSynthesisSupported,
  readStoredSpeechLang,
  speak,
  SPEECH_LANG_STORAGE_KEY,
  startListening,
  stopSpeaking,
  SUPPORTED_SPEECH_LANGS,
} from "../lib/speech";
import ChatSidebar, { type ChatSummary } from "../components/ChatSidebar";
import ChatBubbleAssistant from "../components/ChatBubbleAssistant";
import { IconMic, IconPaperclip, IconPanelLeft, IconSend, IconVolume } from "../components/icons";

interface BubbleItem {
  kind: "bubble";
  id: string;
  role: "user" | "assistant";
  text: string;
}
interface ToolItem {
  kind: "tool";
  id: string;
  name: string;
  input: unknown;
  result?: string;
}
type ChatItem = BubbleItem | ToolItem;

interface PersistedMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  tool_calls: { id: string; name: string; input: unknown; result?: string }[] | null;
}

interface ChatDetail extends ChatSummary {
  messages: PersistedMessage[];
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyEvent = any;

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(2) + " " + sizes[i];
}

export default function Chat() {
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();

  const firstRef = useRef(true);
  const sseRef = useRef<EventSource | null>(null);
  const currentAssistantId = useRef<string | null>(null);
  const currentAssistantTextRef = useRef("");
  const receivedAnyRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const ttsEnabledRef = useRef(false);
  const speechLangRef = useRef<string>(readStoredSpeechLang());
  const recognitionRef = useRef<{ stop: () => void } | null>(null);
  const currentJobIdRef = useRef<string | null>(null);
  const currentChatIdRef = useRef<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const startChatStreamRef = useRef(startChatStream);
  startChatStreamRef.current = startChatStream;

  const [chatMeta, setChatMeta] = useState<ChatDetail | null>(null);
  const [items, setItems] = useState<ChatItem[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [listening, setListening] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [speechLang, setSpeechLang] = useState<string>(() => readStoredSpeechLang());
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);

  useEffect(() => {
    ttsEnabledRef.current = ttsEnabled;
  }, [ttsEnabled]);

  useEffect(() => {
    speechLangRef.current = speechLang;
  }, [speechLang]);

  // No chatId in the URL ("/chat" bare): create a fresh chat and redirect to it.
  useEffect(() => {
    if (chatId) return;
    postJSON<ChatSummary>("/api/chats", {}).then(chat => {
      navigate(`/chat/${chat.id}`, { replace: true });
    });
  }, [chatId, navigate]);

  // Load history whenever we land on a concrete chat.
  useEffect(() => {
    if (!chatId) return;
    currentChatIdRef.current = chatId;
    getJSON<ChatDetail>(`/api/chats/${chatId}`).then(chat => {
      setChatMeta(chat);
      // True until the assistant has actually replied at least once — not just
      // "no messages at all" — so a hard-crashed first attempt (which still
      // persists the user's message) doesn't make the retry use --resume on a
      // claude session that was never created.
      firstRef.current = !chat.messages.some(m => m.role === "assistant");
      const loaded: ChatItem[] = [];
      for (const msg of chat.messages) {
        if (msg.role === "user") {
          loaded.push({ kind: "bubble", id: `m${msg.id}`, role: "user", text: msg.content });
          continue;
        }
        for (const tc of msg.tool_calls ?? []) {
          loaded.push({ kind: "tool", id: tc.id, name: tc.name, input: tc.input, result: tc.result });
        }
        if (msg.content) {
          loaded.push({ kind: "bubble", id: `m${msg.id}`, role: "assistant", text: msg.content });
        }
      }
      setItems(loaded);
      scrollToBottom(true);
    });
  }, [chatId]);

  // Close sidebar on mobile (≤768px) when chat is selected via navigation
  const prevChatId = useRef(chatId);
  if (chatId && chatId !== prevChatId.current) {
    prevChatId.current = chatId;
    if (window.innerWidth <= 768) {
      setSidebarOpen(false);
    }
  }

  // Reconnect SSE when visibility changes: when the app comes back to foreground,
  // always reconcile with server state to recover any messages that arrived while backgrounded.
  // If the job is still running, reconnect the stream to continue receiving updates.
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.visibilityState !== "visible" || !currentChatIdRef.current) {
        return;
      }

      try {
        // Fetch current chat state from server
        const chat = await getJSON<ChatDetail>(`/api/chats/${currentChatIdRef.current}`);

        // Rebuild items from server state (full replace to avoid ID mismatches)
        const loaded: ChatItem[] = [];
        for (const msg of chat.messages) {
          if (msg.role === "user") {
            loaded.push({ kind: "bubble", id: `m${msg.id}`, role: "user", text: msg.content });
            continue;
          }
          for (const tc of msg.tool_calls ?? []) {
            loaded.push({ kind: "tool", id: tc.id, name: tc.name, input: tc.input, result: tc.result });
          }
          if (msg.content) {
            loaded.push({ kind: "bubble", id: `m${msg.id}`, role: "assistant", text: msg.content });
          }
        }
        setItems(loaded);
        scrollToBottom();

        // If there's an active job still running, reconnect the stream to catch live updates
        if (currentJobIdRef.current && sseRef.current === null) {
          try {
            const job = await getJSON<{ status: string }>(`/api/jobs/${currentJobIdRef.current}`);
            if (job.status === "running" || job.status === "queued") {
              // Job is still active; reconnect to the stream
              startChatStreamRef.current(currentJobIdRef.current);
            } else {
              // Job finished; just mark sending as done
              setSending(false);
              currentJobIdRef.current = null;
            }
          } catch {
            // Job not found or error getting status; assume it's done
            setSending(false);
            currentJobIdRef.current = null;
          }
        } else {
          // No active job, just stop sending state
          setSending(false);
        }
      } catch (err) {
        console.error("Failed to reconcile chat state after backgrounding:", err);
        // Don't crash; let UI stay stable
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [chatId]);

  function scrollToBottom(smooth: boolean = false) {
    requestAnimationFrame(() => {
      bottomRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'end' });
    });
  }

  function addBubble(role: "user" | "assistant", text: string): string {
    const id = uuid();
    setItems(prev => [...prev, { kind: "bubble", id, role, text }]);
    scrollToBottom();
    return id;
  }

  function appendToAssistant(id: string, delta: string) {
    setItems(prev =>
      prev.map(it => (it.kind === "bubble" && it.id === id ? { ...it, text: it.text + delta } : it)),
    );
    scrollToBottom();
  }

  function addToolCall(id: string, name: string, input: unknown) {
    setItems(prev => [...prev, { kind: "tool", id, name, input }]);
    scrollToBottom();
  }

  function fillToolResult(id: string, resultText: string) {
    const truncated = resultText.length > 2000 ? resultText.slice(0, 2000) + "…" : resultText;
    setItems(prev => prev.map(it => (it.kind === "tool" && it.id === id ? { ...it, result: truncated } : it)));
    scrollToBottom();
  }

  function handleChatEvent(evt: AnyEvent) {
    if (evt.type === "stream_event" && evt.event?.type === "content_block_delta") {
      const delta = evt.event.delta;
      if (delta?.type === "text_delta") {
        receivedAnyRef.current = true;
        if (!currentAssistantId.current) {
          currentAssistantId.current = addBubble("assistant", "");
          currentAssistantTextRef.current = "";
        }
        currentAssistantTextRef.current += delta.text;
        appendToAssistant(currentAssistantId.current, delta.text);
      }
      return;
    }

    if (evt.type === "assistant" && evt.message?.content) {
      receivedAnyRef.current = true;
      for (const block of evt.message.content) {
        if (block.type === "text" && !currentAssistantId.current) {
          addBubble("assistant", block.text);
        } else if (block.type === "tool_use") {
          addToolCall(block.id, block.name, block.input);
        }
      }
      if (currentAssistantId.current && ttsEnabledRef.current && currentAssistantTextRef.current.trim()) {
        speak(currentAssistantTextRef.current, speechLangRef.current);
      }
      currentAssistantTextRef.current = "";
      currentAssistantId.current = null;
      return;
    }

    if (evt.type === "user" && evt.message?.content) {
      for (const block of evt.message.content) {
        if (block.type === "tool_result") {
          const text = typeof block.content === "string" ? block.content : JSON.stringify(block.content);
          fillToolResult(block.tool_use_id, text);
        }
      }
      return;
    }

    if (evt.type === "result") {
      currentAssistantId.current = null;
      firstRef.current = false;
    }
  }

  function startChatStream(jobId: string) {
    sseRef.current?.close();
    currentJobIdRef.current = jobId;
    let retries = 0;
    const MAX_RETRIES = 5;

    function connect() {
      sseRef.current?.close();
      const sse = new EventSource(`/api/jobs/${jobId}/stream`);
      sseRef.current = sse;

      sse.onmessage = e => {
        retries = 0;
        let line: string;
        try {
          line = JSON.parse(e.data);
        } catch {
          return;
        }
        if (!line) return;
        let evt: AnyEvent;
        try {
          evt = JSON.parse(line);
        } catch {
          return;
        }
        handleChatEvent(evt);
      };

      sse.addEventListener("done", () => {
        sse.close();
        sseRef.current = null;
        currentJobIdRef.current = null;
        setSending(false);
        if (!receivedAnyRef.current) {
          addBubble("assistant", "⚠️ No se obtuvo respuesta. Probá reenviar el mensaje.");
        }
        setRefreshKey(k => k + 1);
      });

      sse.onerror = () => {
        sse.close();
        if (retries < MAX_RETRIES) {
          retries++;
          const delay = Math.min(1000 * 2 ** retries, 30000);
          setTimeout(connect, delay);
        } else {
          sseRef.current = null;
          currentJobIdRef.current = null;
          setSending(false);
        }
      };
    }

    connect();
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.currentTarget.files;
    if (files) {
      const newFiles = Array.from(files);

      // Validations
      const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
      const MAX_TOTAL_SIZE = 50 * 1024 * 1024; // 50 MB
      const MAX_FILES = 10;

      // Check count
      const totalFiles = attachedFiles.length + newFiles.length;
      if (totalFiles > MAX_FILES) {
        addBubble("assistant", `Demasiados archivos. Máximo ${MAX_FILES} archivos por envío.`);
        e.currentTarget.value = "";
        return;
      }

      // Check individual file sizes
      for (const file of newFiles) {
        if (file.size > MAX_FILE_SIZE) {
          addBubble("assistant", `El archivo '${file.name}' es demasiado grande. Máximo ${MAX_FILE_SIZE / (1024 * 1024)} MB por archivo.`);
          e.currentTarget.value = "";
          return;
        }
      }

      // Check total size
      const totalSize = attachedFiles.reduce((sum, f) => sum + f.size, 0) + newFiles.reduce((sum, f) => sum + f.size, 0);
      if (totalSize > MAX_TOTAL_SIZE) {
        addBubble("assistant", `El tamaño total de los archivos excede el límite. Máximo ${MAX_TOTAL_SIZE / (1024 * 1024)} MB en total.`);
        e.currentTarget.value = "";
        return;
      }

      setAttachedFiles(prev => [...prev, ...newFiles]);
    }
    e.currentTarget.value = "";
  }

  function removeAttachedFile(index: number) {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  }

  async function uploadFiles(files: File[]): Promise<string[]> {
    if (!chatId || files.length === 0) return [];

    // Secondary validation (defense-in-depth)
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
    const MAX_TOTAL_SIZE = 50 * 1024 * 1024; // 50 MB
    const MAX_FILES = 10;

    if (files.length > MAX_FILES) {
      throw new Error(`Demasiados archivos. Máximo ${MAX_FILES} archivos por envío.`);
    }

    for (const file of files) {
      if (file.size > MAX_FILE_SIZE) {
        throw new Error(`El archivo '${file.name}' es demasiado grande. Máximo ${MAX_FILE_SIZE / (1024 * 1024)} MB por archivo.`);
      }
    }

    const totalSize = files.reduce((sum, f) => sum + f.size, 0);
    if (totalSize > MAX_TOTAL_SIZE) {
      throw new Error(`El tamaño total de los archivos excede el límite. Máximo ${MAX_TOTAL_SIZE / (1024 * 1024)} MB en total.`);
    }

    const formData = new FormData();
    files.forEach(file => formData.append("files", file));

    const res = await fetch(`/api/files/upload?chat_id=${encodeURIComponent(chatId)}`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const error = await res.text();
      throw new Error(`Upload failed: ${res.status} ${error}`);
    }

    const data = await res.json();
    return data.file_paths || [];
  }

  async function sendChatMessage() {
    const message = input.trim();
    if (!message || !chatId) return;
    setInput("");
    setSending(true);

    let filePaths: string[] = [];
    if (attachedFiles.length > 0) {
      setUploading(true);
      try {
        filePaths = await uploadFiles(attachedFiles);
        setAttachedFiles([]);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        addBubble("assistant", `Error al subir archivos: ${errorMsg}`);
        setSending(false);
        setUploading(false);
        return;
      } finally {
        setUploading(false);
      }
    }

    addBubble("user", message);
    currentAssistantId.current = null;
    receivedAnyRef.current = false;

    const res = await fetch("/api/chat/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: chatId,
        message,
        first: firstRef.current,
        project_id: chatMeta?.project_id ?? null,
        file_paths: filePaths.length > 0 ? filePaths : null,
      }),
    });
    if (!res.ok) {
      addBubble("assistant", "Error al enviar el mensaje.");
      setSending(false);
      return;
    }
    const { job_id } = await res.json();
    startChatStream(job_id);
  }

  function toggleListening() {
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }
    const handle = startListening(
      text => setInput(prev => (prev ? `${prev} ${text}` : text)),
      () => {
        setListening(false);
        recognitionRef.current = null;
      },
      speechLang,
    );
    if (handle) {
      recognitionRef.current = handle;
      setListening(true);
    }
  }

  function toggleTts() {
    setTtsEnabled(prev => {
      if (prev) stopSpeaking();
      return !prev;
    });
  }

  function handleSpeechLangChange(lang: string) {
    setSpeechLang(lang);
    localStorage.setItem(SPEECH_LANG_STORAGE_KEY, lang);
  }

  return (
    <>
      <button
        className="icon-btn md:hidden mb-2"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label={sidebarOpen ? "Cerrar historial" : "Abrir historial"}
        aria-expanded={sidebarOpen}
        title={sidebarOpen ? "Cerrar historial" : "Abrir historial"}
      >
        <IconPanelLeft />
      </button>
      <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-4 items-stretch h-[calc(100dvh-7rem)]">
        <div className={sidebarOpen ? "block" : "hidden md:block"}>
          <ChatSidebar activeChatId={chatId} refreshKey={refreshKey} />
        </div>
        <div className="flex flex-col gap-3 h-full min-h-0">
        <div ref={scrollRef} className="chat-scroll">
          {items.map(item =>
            item.kind === "tool" ? (
              <details key={item.id} className="tool-call">
                <summary>{item.name}</summary>
                <pre>{JSON.stringify(item.input, null, 2)}</pre>
                {item.result !== undefined && <pre className="text-text-muted">{item.result}</pre>}
              </details>
            ) : item.role === "assistant" ? (
              <ChatBubbleAssistant key={item.id} id={item.id} text={item.text} />
            ) : (
              <div key={item.id} className="chat-bubble user">
                {item.text}
              </div>
            ),
          )}
          {sending && (
            <div className="chat-bubble assistant typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-2">
            {attachedFiles.map((file, idx) => (
              <div
                key={`${file.name}-${idx}`}
                className="chat-attachment-chip"
                role="listitem"
                aria-label={`Archivo adjunto: ${file.name}, ${formatFileSize(file.size)}`}
              >
                <IconPaperclip className="w-3.5 h-3.5" />
                {file.name} ({formatFileSize(file.size)})
                <button
                  type="button"
                  className="text-text-muted hover:text-text cursor-pointer focus:ring-2 focus:ring-accent focus:ring-offset-2"
                  onClick={() => removeAttachedFile(idx)}
                  title="Remover archivo"
                  aria-label={`Remover archivo ${file.name}`}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
        {uploading && (
          <div className="text-center text-sm text-text-muted">
            Subiendo archivos...
          </div>
        )}
        <div className="chat-composer">
          <button
            type="button"
            className="icon-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Adjuntar archivos"
            aria-label="Adjuntar archivos"
            disabled={uploading}
          >
            <IconPaperclip />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            style={{ display: "none" }}
            aria-label="Seleccionar archivos para adjuntar"
          />
          <input
            className="chat-composer-input"
            value={input}
            placeholder="Escribí un mensaje..."
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === "Enter" && !uploading) sendChatMessage();
            }}
            disabled={uploading}
          />
          {(isSpeechRecognitionSupported() || isSpeechSynthesisSupported()) && (
            <select
              className="chat-composer-lang-select"
              value={speechLang}
              onChange={e => handleSpeechLangChange(e.target.value)}
              title="Idioma de voz"
              disabled={uploading}
              aria-label="Seleccionar idioma de voz"
            >
              {SUPPORTED_SPEECH_LANGS.map(lang => (
                <option key={lang} value={lang}>
                  {lang}
                </option>
              ))}
            </select>
          )}
          <button
            type="button"
            className={`icon-btn mic-btn ${listening ? "recording" : ""}`}
            onClick={toggleListening}
            disabled={!isSpeechRecognitionSupported() || uploading}
            title={
              !isSpeechRecognitionSupported()
                ? "Requiere HTTPS o navegador compatible"
                : listening ? "Detener dictado" : "Dictar por voz"
            }
            aria-label={
              !isSpeechRecognitionSupported()
                ? "Requiere HTTPS o navegador compatible"
                : listening ? "Detener dictado" : "Dictar por voz"
            }
          >
            <IconMic />
          </button>
          <button
            type="button"
            className={`icon-btn tts-btn ${ttsEnabled ? "active" : ""}`}
            onClick={toggleTts}
            disabled={!isSpeechSynthesisSupported() || uploading}
            title={
              !isSpeechSynthesisSupported()
                ? "Requiere HTTPS o navegador compatible"
                : ttsEnabled ? "Desactivar lectura en voz alta" : "Leer respuestas en voz alta"
            }
            aria-label={
              !isSpeechSynthesisSupported()
                ? "Requiere HTTPS o navegador compatible"
                : ttsEnabled ? "Desactivar lectura en voz alta" : "Leer respuestas en voz alta"
            }
          >
            <IconVolume />
          </button>
          <button
            className="icon-btn icon-btn-send"
            disabled={sending || !chatId || uploading}
            onClick={sendChatMessage}
            aria-label={uploading ? "Subiendo archivos..." : "Enviar mensaje"}
          >
            <IconSend />
          </button>
        </div>
      </div>
      </div>
    </>
  );
}
