import { describe, it, expect, beforeEach, vi } from 'vitest'
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Chat from './Chat'
import * as api from '../lib/api'

// Mock the api module
vi.mock('../lib/api', () => ({
  getJSON: vi.fn(),
  postJSON: vi.fn(),
}))

// Mock the speech module
vi.mock('../lib/speech', () => ({
  isSpeechRecognitionSupported: () => false,
  isSpeechSynthesisSupported: () => false,
  readStoredSpeechLang: () => 'es-ES',
  speak: vi.fn(),
  stopSpeaking: vi.fn(),
  startListening: vi.fn(),
  SPEECH_LANG_STORAGE_KEY: 'speech-lang',
  SUPPORTED_SPEECH_LANGS: ['es-ES', 'en-US'],
}))

// Mock ChatSidebar component
vi.mock('../components/ChatSidebar', () => ({
  default: () => <div data-testid="chat-sidebar">Sidebar</div>,
}))

// Mock ChatBubbleAssistant component
vi.mock('../components/ChatBubbleAssistant', () => ({
  default: ({ text }: { text: string }) => <div data-testid="chat-bubble-assistant">{text}</div>,
}))

describe('Chat Component', () => {
  const mockChatId = 'chat-123'
  const mockChatDetail = {
    id: mockChatId,
    title: 'Test Chat',
    created_at: 1234567890,
    project_id: null,
    messages: [],
  }

  beforeEach(() => {
    vi.clearAllMocks()
    ;(api.getJSON as any).mockResolvedValue(mockChatDetail)
    ;(api.postJSON as any).mockResolvedValue({ id: 'new-chat' })
  })

  it('renders input field when on a chat page', async () => {
    render(
      <MemoryRouter initialEntries={[`/chat/${mockChatId}`]}>
        <Chat />
      </MemoryRouter>
    )

    const input = await waitFor(() =>
      screen.getByPlaceholderText('Escribí un mensaje...')
    )
    expect(input).toBeInTheDocument()
  })

  it('input field is editable', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={[`/chat/${mockChatId}`]}>
        <Chat />
      </MemoryRouter>
    )

    const input = await waitFor(() =>
      screen.getByPlaceholderText('Escribí un mensaje...') as HTMLInputElement
    )

    await user.type(input, 'Test message')
    expect(input.value).toBe('Test message')
  })

  it('send button exists', async () => {
    render(
      <MemoryRouter initialEntries={[`/chat/${mockChatId}`]}>
        <Chat />
      </MemoryRouter>
    )

    await waitFor(() => {
      const sendButton = screen.getByRole('button', { name: /enviar/i })
      expect(sendButton).toBeInTheDocument()
    })
  })

  it('renders file attach button', async () => {
    render(
      <MemoryRouter initialEntries={[`/chat/${mockChatId}`]}>
        <Chat />
      </MemoryRouter>
    )

    await waitFor(() => {
      const attachButton = screen.getByLabelText('Adjuntar archivos')
      expect(attachButton).toBeInTheDocument()
    })
  })

  it('renders microphone button', async () => {
    render(
      <MemoryRouter initialEntries={[`/chat/${mockChatId}`]}>
        <Chat />
      </MemoryRouter>
    )

    await waitFor(() => {
      const micButtons = screen.getAllByRole('button')
      const micButton = micButtons.find(btn => btn.className?.includes('mic-btn'))
      expect(micButton).toBeInTheDocument()
    })
  })

  it('renders speaker button for text-to-speech', async () => {
    render(
      <MemoryRouter initialEntries={[`/chat/${mockChatId}`]}>
        <Chat />
      </MemoryRouter>
    )

    await waitFor(() => {
      const ttsButtons = screen.getAllByRole('button')
      const ttsButton = ttsButtons.find(btn => btn.className?.includes('tts-btn'))
      expect(ttsButton).toBeInTheDocument()
    })
  })

  it('input gets cleared after typing', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={[`/chat/${mockChatId}`]}>
        <Chat />
      </MemoryRouter>
    )

    const input = await waitFor(() =>
      screen.getByPlaceholderText('Escribí un mensaje...') as HTMLInputElement
    )

    await user.type(input, 'Test')
    expect(input.value).toBe('Test')

    await user.clear(input)
    expect(input.value).toBe('')
  })

  it('renders sidebar component', async () => {
    render(
      <MemoryRouter initialEntries={[`/chat/${mockChatId}`]}>
        <Chat />
      </MemoryRouter>
    )

    await waitFor(() => {
      const sidebar = screen.getByTestId('chat-sidebar')
      expect(sidebar).toBeInTheDocument()
    })
  })
})
