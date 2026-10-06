import { useState } from 'react'

export default function Composer({ onSend, disabled }) {
  const [text, setText] = useState('')

  function submit(e) {
    e.preventDefault()
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  return (
    <form className="composer" onSubmit={submit}>
      <input
        aria-label="Type your question"
        value={text}
        placeholder="Ask about an order, ticket, return or warranty..."
        onChange={(e) => setText(e.target.value)}
        maxLength={300}
      />
      <button type="submit" disabled={disabled || !text.trim()}>Send</button>
    </form>
  )
}