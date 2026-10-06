function renderBold(text) {
  return text
    .split(/\*\*(.+?)\*\*/g)
    .map((part, i) => (i % 2 ? <strong key={i}>{part}</strong> : part))
}

export default function MessageBubble({ role, text }) {
  return (
    <div className={`bubble ${role}`}>
      {renderBold(text)}
    </div>
  )
}