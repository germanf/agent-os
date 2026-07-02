// Feature-detection wrappers for the Web Speech API (mic input / spoken output).
// SpeechRecognition requires a secure context (HTTPS/localhost) in most browsers —
// same constraint that motivated the crypto.randomUUID() fallback in uuid.ts.

// Minimal shape of the bits of the Web Speech API we actually use — the
// official SpeechRecognition types aren't part of this project's TS DOM lib.
interface SpeechRecognitionResultLike {
  [index: number]: { transcript: string };
}
interface SpeechRecognitionEventLike {
  results: ArrayLike<SpeechRecognitionResultLike>;
}
interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  start(): void;
  stop(): void;
}
type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

// The whole dashboard UI is in (Argentine) Spanish, so default both STT and
// TTS to it explicitly — navigator.language reflects the browser/OS locale,
// which is very often "en-US" regardless of what language the user actually
// speaks, and silently mis-recognizing Spanish audio as English gives
// garbled, unrelated-looking transcripts rather than an obvious error.
// Users can override this via the language selector in Chat.tsx.
export const DEFAULT_SPEECH_LANG = "es-AR";

export const SUPPORTED_SPEECH_LANGS = ["es-AR", "es-ES", "es-MX", "en-US", "pt-BR"] as const;
export type SpeechLang = (typeof SUPPORTED_SPEECH_LANGS)[number];

export const SPEECH_LANG_STORAGE_KEY = "chat-speech-lang";

export function readStoredSpeechLang(): SpeechLang {
  const stored = localStorage.getItem(SPEECH_LANG_STORAGE_KEY);
  return (SUPPORTED_SPEECH_LANGS as readonly string[]).includes(stored ?? "")
    ? (stored as SpeechLang)
    : DEFAULT_SPEECH_LANG;
}

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  const w = window as typeof window & {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function isSpeechRecognitionSupported(): boolean {
  return getSpeechRecognitionCtor() !== null;
}

export function startListening(
  onResult: (text: string) => void,
  onEnd: () => void,
  lang: string = DEFAULT_SPEECH_LANG,
): { stop: () => void } | null {
  const Ctor = getSpeechRecognitionCtor();
  if (!Ctor) return null;

  const recognition = new Ctor();
  recognition.lang = lang;
  recognition.interimResults = false;
  recognition.continuous = false;

  recognition.onresult = (event: SpeechRecognitionEventLike) => {
    const transcript = Array.from(event.results)
      .map(result => result[0].transcript)
      .join(" ");
    onResult(transcript);
  };
  recognition.onend = onEnd;
  recognition.onerror = onEnd;

  recognition.start();
  return { stop: () => recognition.stop() };
}

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

// Chrome (and others) return an empty voice list until the async
// "voiceschanged" event fires the first time, so a naive getVoices() call
// right after a TTS toggle can silently miss every installed voice.
function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  const existing = window.speechSynthesis.getVoices();
  if (existing.length > 0) return Promise.resolve(existing);

  return new Promise(resolve => {
    const timeout = setTimeout(() => resolve(window.speechSynthesis.getVoices()), 1000);
    window.speechSynthesis.onvoiceschanged = () => {
      clearTimeout(timeout);
      resolve(window.speechSynthesis.getVoices());
    };
  });
}

const HIGH_QUALITY_VOICE_NAME = /google|enhanced|premium|neural/i;

function pickVoice(voices: SpeechSynthesisVoice[], lang: string): SpeechSynthesisVoice | null {
  if (voices.length === 0) return null;
  const baseLang = lang.split("-")[0];
  const exactMatches = voices.filter(v => v.lang === lang);
  const baseMatches = voices.filter(v => v.lang.split("-")[0] === baseLang);
  const candidates = exactMatches.length > 0 ? exactMatches : baseMatches;
  if (candidates.length === 0) return null;
  return candidates.find(v => HIGH_QUALITY_VOICE_NAME.test(v.name)) ?? candidates[0];
}

export async function speak(text: string, lang: string = DEFAULT_SPEECH_LANG): Promise<void> {
  if (!isSpeechSynthesisSupported() || !text.trim()) return;
  window.speechSynthesis.cancel(); // don't stack overlapping utterances
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang;
  utterance.rate = 0.95; // slightly slower than default for better intelligibility
  const voice = pickVoice(await loadVoices(), lang);
  if (voice) utterance.voice = voice;
  window.speechSynthesis.speak(utterance);
}

export function stopSpeaking(): void {
  if (isSpeechSynthesisSupported()) window.speechSynthesis.cancel();
}
