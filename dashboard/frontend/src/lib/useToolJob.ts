import { useCallback, useRef, useState } from "react";

export type JobState = "queued" | "running" | "done" | "failed" | "cancelled";

export interface JobSummary {
  id: string;
  tool: string;
  status: JobState;
  exit_code: number | null;
  started_at: number;
  ended_at: number | null;
  line_count: number;
}

/** Drives the log console + status badge for one tool tab (api/scraper), mirroring
 * the old app.js `state[tool]` object — each tab gets its own independent instance. */
export function useToolJob() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [lines, setLines] = useState<string[]>([]);
  const [status, setStatus] = useState<JobState | null>(null);
  const sseRef = useRef<EventSource | null>(null);

  const fetchStatus = useCallback(async (id: string) => {
    const res = await fetch(`/api/jobs/${id}`);
    if (!res.ok) return null;
    const job: JobSummary = await res.json();
    setStatus(job.status);
    return job;
  }, []);

  const start = useCallback(
    (id: string, onDone?: () => void) => {
      setJobId(id);
      setLines([]);
      setStatus("running");
      sseRef.current?.close();

      const sse = new EventSource(`/api/jobs/${id}/stream`);
      sseRef.current = sse;

      sse.onmessage = e => {
        try {
          const line = JSON.parse(e.data) as string;
          setLines(prev => [...prev, line]);
        } catch {
          // ignore malformed lines
        }
      };

      sse.addEventListener("done", () => {
        sse.close();
        sseRef.current = null;
        fetchStatus(id);
        onDone?.();
      });

      sse.onerror = () => {
        sse.close();
        sseRef.current = null;
        fetchStatus(id);
      };
    },
    [fetchStatus],
  );

  const viewLogs = useCallback(
    async (id: string) => {
      setJobId(id);
      const res = await fetch(`/api/jobs/${id}/logs`);
      const existing: string[] = res.ok ? await res.json() : [];
      setLines(existing);
      const job = await fetchStatus(id);
      if (job?.status === "running") start(id);
    },
    [fetchStatus, start],
  );

  const cancel = useCallback(async () => {
    if (!jobId) return;
    await fetch(`/api/jobs/${jobId}/cancel`, { method: "POST" });
    sseRef.current?.close();
    sseRef.current = null;
    fetchStatus(jobId);
  }, [jobId, fetchStatus]);

  const clear = useCallback(() => setLines([]), []);

  return { jobId, lines, status, start, viewLogs, cancel, clear };
}
