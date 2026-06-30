import { useEffect, useRef, useState, type ReactNode } from "react";
import ReactDOM from "react-dom";

interface PendingConfirm {
  message: string;
  resolve: (value: boolean) => void;
}

export function useConfirm(): { confirm: (message: string) => Promise<boolean>; dialogElement: ReactNode } {
  const [pending, setPending] = useState<PendingConfirm | null>(null);
  const settledRef = useRef(false);

  function confirm(message: string): Promise<boolean> {
    return new Promise(resolve => {
      settledRef.current = false;
      setPending({ message, resolve });
    });
  }

  function settle(value: boolean) {
    if (settledRef.current) return;
    settledRef.current = true;
    pending?.resolve(value);
    setPending(null);
  }

  useEffect(() => {
    if (!pending) return;

    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        settle(false);
      }
    };

    document.addEventListener("keydown", handleEscapeKey);
    return () => {
      document.removeEventListener("keydown", handleEscapeKey);
    };
  }, [pending]);

  const dialogElement = pending
    ? ReactDOM.createPortal(
        <div
          className="modal-backdrop"
          onClick={() => settle(false)}
          role="dialog"
          aria-modal="true"
        >
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <p className="mb-4">{pending.message}</p>
            <div className="flex gap-2 justify-end">
              <button className="btn btn-ghost" onClick={() => settle(false)} autoFocus>
                Cancelar
              </button>
              <button className="btn btn-danger" onClick={() => settle(true)}>
                Eliminar
              </button>
            </div>
          </div>
        </div>,
        document.body,
      )
    : null;

  return { confirm, dialogElement };
}
