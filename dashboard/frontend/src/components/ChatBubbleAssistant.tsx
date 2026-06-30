import { useState } from "react";
import { copyToClipboard } from "../lib/clipboard";
import { parseAndSanitize } from "../lib/sanitize";

interface ChatBubbleAssistantProps {
  id: string;
  text: string;
}

type CopyStatus = "idle" | "copied" | "error";

export default function ChatBubbleAssistant({ text }: ChatBubbleAssistantProps) {
  const [copyStatus, setCopyStatus] = useState<CopyStatus>("idle");

  const handleCopy = async () => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopyStatus("copied");
      setTimeout(() => setCopyStatus("idle"), 1500);
    } else {
      setCopyStatus("error");
      setTimeout(() => setCopyStatus("idle"), 2500);
    }
  };

  const sanitizedHtml = parseAndSanitize(text);

  return (
    <div className="relative group inline-block w-full">
      <div
        className="chat-bubble assistant"
        dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
      />
      <button
        type="button"
        onClick={handleCopy}
        className="chat-bubble-copy-btn"
        title={
          copyStatus === "error"
            ? "Error al copiar"
            : copyStatus === "copied"
              ? "Copiado"
              : "Copiar al clipboard"
        }
        aria-label="Copiar respuesta"
      >
        {copyStatus === "copied" ? "✓" : copyStatus === "error" ? "✗" : "📋"}
      </button>
    </div>
  );
}
