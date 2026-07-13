import { useState, type FormEvent } from 'react';
import { api } from '../api/client';
import type { ChatMessage } from '../types';
import './ChatWidget.css';

interface ChatReply {
  reply: string;
  used_fallback: boolean;
}

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: "Hi! I'm the Tutti Frutti assistant — ask me about our fruit." },
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const history = messages.slice(-10);
    const nextMessages: ChatMessage[] = [...messages, { role: 'user', content: trimmed }];
    setMessages(nextMessages);
    setInput('');
    setIsSending(true);
    setError(null);

    try {
      const response = await api.post<ChatReply>('/assistant/chat', {
        message: trimmed,
        history,
      });
      setMessages((prev) => [...prev, { role: 'assistant', content: response.reply }]);
    } catch {
      setError("Couldn't reach the assistant. Please try again.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="chat-widget" data-testid="chat-widget">
      {isOpen && (
        <div className="chat-widget__panel" data-testid="chat-panel">
          <div className="chat-widget__header">
            <span>Fruit Assistant</span>
            <button
              className="chat-widget__close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
              data-testid="chat-close-button"
            >
              ✕
            </button>
          </div>

          <div className="chat-widget__messages" data-testid="chat-messages">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`chat-widget__message chat-widget__message--${message.role}`}
                data-testid={`chat-message-${message.role}`}
              >
                {message.content}
              </div>
            ))}
            {isSending && (
              <div className="chat-widget__message chat-widget__message--assistant chat-widget__message--pending" data-testid="chat-message-pending">
                Thinking…
              </div>
            )}
          </div>

          {error && <p className="chat-widget__error" data-testid="chat-error">{error}</p>}

          <form className="chat-widget__form" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about our fruit…"
              aria-label="Chat message"
              data-testid="chat-input"
            />
            <button type="submit" className="btn-primary" disabled={isSending} data-testid="chat-send-button">
              Send
            </button>
          </form>
        </div>
      )}

      <button
        className="chat-widget__toggle"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? 'Close fruit assistant chat' : 'Open fruit assistant chat'}
        data-testid="chat-toggle-button"
      >
        {isOpen ? '✕' : '🍓 Ask us'}
      </button>
    </div>
  );
}
