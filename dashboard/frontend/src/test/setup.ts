import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.fetch if needed
global.fetch = vi.fn()

// Mock EventSource for SSE tests
class MockEventSource {
  constructor(public url: string) {}
  addEventListener = vi.fn()
  removeEventListener = vi.fn()
  close = vi.fn()
}
global.EventSource = MockEventSource as any
