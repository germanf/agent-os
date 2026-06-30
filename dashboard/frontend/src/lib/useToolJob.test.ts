import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useToolJob, type JobSummary } from './useToolJob'

describe('useToolJob', () => {
  const mockJobId = 'job-123'
  const mockJobSummary: JobSummary = {
    id: mockJobId,
    tool: 'scrapers',
    status: 'done',
    exit_code: 0,
    started_at: 1234567890,
    ended_at: 1234567900,
    line_count: 42,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it('initializes with null jobId and empty lines', () => {
    const { result } = renderHook(() => useToolJob())

    expect(result.current.jobId).toBeNull()
    expect(result.current.lines).toEqual([])
    expect(result.current.status).toBeNull()
  })

  it('updates status when viewLogs is called with done job', async () => {
    ;(global.fetch as any).mockImplementation((url: string) => {
      if (url === `/api/jobs/${mockJobId}/logs`) {
        return Promise.resolve({
          ok: true,
          json: async () => [],
        })
      }
      if (url === `/api/jobs/${mockJobId}`) {
        return Promise.resolve({
          ok: true,
          json: async () => mockJobSummary,
        })
      }
      return Promise.reject(new Error(`Unexpected URL: ${url}`))
    })

    const { result } = renderHook(() => useToolJob())

    await act(async () => {
      await result.current.viewLogs(mockJobId)
    })

    expect(result.current.status).toBe('done')
  })

  it('handles viewLogs when fetch fails gracefully', async () => {
    ;(global.fetch as any).mockImplementation((url: string) => {
      if (url === `/api/jobs/${mockJobId}/logs`) {
        return Promise.resolve({
          ok: false,
        })
      }
      if (url === `/api/jobs/${mockJobId}`) {
        return Promise.resolve({
          ok: false,
        })
      }
      return Promise.reject(new Error(`Unexpected URL: ${url}`))
    })

    const { result } = renderHook(() => useToolJob())

    await act(async () => {
      await result.current.viewLogs(mockJobId)
    })

    // Should have empty lines and null status when fetch fails
    expect(result.current.lines).toEqual([])
    expect(result.current.status).toBeNull()
  })

  it('starts a job and sets status to running', async () => {
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockJobSummary,
    })

    const { result } = renderHook(() => useToolJob())

    act(() => {
      result.current.start(mockJobId)
    })

    expect(result.current.jobId).toBe(mockJobId)
    expect(result.current.status).toBe('running')
    expect(result.current.lines).toEqual([])
  })

  it('handles EventSource messages and appends lines', async () => {
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockJobSummary,
    })

    const { result } = renderHook(() => useToolJob())

    let onmessage: any
    let addEventListener: any

    // Mock EventSource
    global.EventSource = class {
      constructor(public url: string) {}
      onmessage: any
      addEventListener = (event: string, callback: any) => {
        if (event === 'done') {
          addEventListener = callback
        }
      }
      close = vi.fn()
      onerror: any
    } as any

    act(() => {
      result.current.start(mockJobId)
    })

    // Simulate receiving a message
    const mockEventSource = (global as any).EventSource
    const instance = new mockEventSource(`/api/jobs/${mockJobId}/stream`)

    expect(instance.url).toBe(`/api/jobs/${mockJobId}/stream`)
  })

  it('closes EventSource on cancel', async () => {
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ ...mockJobSummary, status: 'cancelled' }),
    })

    const { result } = renderHook(() => useToolJob())

    act(() => {
      result.current.start(mockJobId)
    })

    expect(result.current.jobId).toBe(mockJobId)

    await act(async () => {
      await result.current.cancel()
    })

    expect(global.fetch).toHaveBeenCalledWith(
      `/api/jobs/${mockJobId}/cancel`,
      { method: 'POST' }
    )
  })

  it('clears lines without changing jobId', () => {
    const { result } = renderHook(() => useToolJob())

    act(() => {
      result.current.start(mockJobId)
    })

    expect(result.current.jobId).toBe(mockJobId)

    act(() => {
      result.current.clear()
    })

    expect(result.current.lines).toEqual([])
    expect(result.current.jobId).toBe(mockJobId)
  })

  it('viewLogs with running job starts the stream', async () => {
    const mockLogs = ['line 1', 'line 2', 'line 3']
    ;(global.fetch as any).mockImplementation((url: string) => {
      if (url === `/api/jobs/${mockJobId}/logs`) {
        return Promise.resolve({
          ok: true,
          json: async () => mockLogs,
        })
      }
      if (url === `/api/jobs/${mockJobId}`) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ ...mockJobSummary, status: 'running' }),
        })
      }
      return Promise.reject(new Error(`Unexpected URL: ${url}`))
    })

    const { result } = renderHook(() => useToolJob())

    await act(async () => {
      await result.current.viewLogs(mockJobId)
    })

    expect(result.current.jobId).toBe(mockJobId)
    expect(result.current.status).toBe('running')
  })

  it('cancel is no-op when no jobId is set', async () => {
    const { result } = renderHook(() => useToolJob())

    await act(async () => {
      await result.current.cancel()
    })

    expect(global.fetch).not.toHaveBeenCalled()
  })
})
