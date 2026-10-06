import { useEffect, useRef, useState } from 'react'
import { sendChat } from '../api.js'
import MessageBubble from './MessageBubble.jsx'
import Composer from './Composer.jsx'

const DEFAULT_CHIPS = ['Show my recent orders', 'Track my order', 'My tickets', 'What can you do?']

export default function ChatWindow({ token, firstName, onExpired }) {
  const welcome = {
    role: 'bot',
    text: `Hi ${firstName}! I can help with your orders, tickets, returns and warranty. What would you like to know?`,
  }
  const [messages, setMessages] = useState([welcome])
  const [chips, setChips] = useState(DEFAULT_CHIPS)
  const [busy, setBusy] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  async function send(text) {
    if (busy) return
    setMessages((m) => [...m, { role: 'user', text }])
    setBusy(true)
    try {
      const data = await sendChat(text, token)
      setMessages((m) => [...m, { role: 'bot', text: data.reply }])
      setChips(data.suggestions?.length ? data.suggestions : DEFAULT_CHIPS)
    } catch (err) {
      if (err.status === 401) {
        onExpired()
        return
      }
      setMessages((m) => [...m, { role: 'bot', text: 'Sorry, something went wrong. Please try again.' }])
    } finally {
      setBusy(false)
    }
  }

  function reset() {
    setMessages([welcome])
    setChips(DEFAULT_CHIPS)
  }

  return (
    <div className="chat card">
      <div className="chat-top">
        <strong>Chat</strong>
        <button className="link" onClick={reset}>Reset conversation</button>
      </div>

      <div className="messages" role="log" aria-live="polite">
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} text={m.text} />
        ))}
        {busy && <div className="bubble bot typing">Typing...</div>}
        <div ref={endRef} />
      </div>

      <div className="chips">
        {chips.map((c) => (
          <button key={c} className="chip" disabled={busy} onClick={() => send(c)}>
            {c}
          </button>
        ))}
      </div>

      <Composer onSend={send} disabled={busy} />
    </div>
  )
}