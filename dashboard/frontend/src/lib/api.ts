export async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`GET ${url} failed: ${res.status}`);
  return res.json();
}

async function sendJSON<T>(method: string, url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = String(res.status);
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {
      // ignore — keep status code as the message
    }
    throw new Error(detail);
  }
  return res.json();
}

export function postJSON<T>(url: string, body: unknown): Promise<T> {
  return sendJSON<T>("POST", url, body);
}

export function patchJSON<T>(url: string, body: unknown): Promise<T> {
  return sendJSON<T>("PATCH", url, body);
}

export function deleteJSON<T>(url: string): Promise<T> {
  return sendJSON<T>("DELETE", url);
}
