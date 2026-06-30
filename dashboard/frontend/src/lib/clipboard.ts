/**
 * Copy text to clipboard with fallback for HTTP contexts.
 *
 * Tries navigator.clipboard API first (HTTPS), falls back to document.execCommand
 * for HTTP contexts where Clipboard API is unavailable.
 *
 * @param text - The text to copy
 * @returns Promise<boolean> - true if copy succeeded, false otherwise
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  // Try Clipboard API (available in HTTPS contexts)
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.error("Clipboard API failed:", err);
    }
  }

  // Fallback: execCommand for HTTP contexts
  try {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    textarea.style.left = "-9999px";
    textarea.style.top = "-9999px";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    const success = document.execCommand("copy");
    document.body.removeChild(textarea);
    return success;
  } catch (err) {
    console.error("execCommand fallback failed:", err);
    return false;
  }
}
