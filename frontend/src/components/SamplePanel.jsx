import { useEffect, useState } from 'react'
import { getSamples } from '../api.js'

export default function SamplePanel({ onUseCredentials }) {
  const [open, setOpen] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    getSamples().then(setData).catch(() => setData(null))
  }, [])

  if (!data) return null

  return (
    <section className="samples card" aria-label="How to test">
      <button
        className="link samples-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        {open ? 'Hide' : 'Show'} "How to test"
      </button>

      {open && (
        <div>
          <p className="muted">Use any of these sample accounts:</p>
          <ul className="sample-list">
            {data.credentials.map((c) => (
              <li key={c.customer_id}>
                <code>{c.customer_id}</code> with <code>{c.order_id}</code>
                {onUseCredentials && (
                  <button
                    className="link"
                    onClick={() => onUseCredentials(c.customer_id, c.order_id)}
                  >
                    Use these
                  </button>
                )}
              </li>
            ))}
          </ul>

          <p className="muted">Example questions:</p>
          <ul>
            {data.questions.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>

          <p className="muted">
            Try a sensitive one too, like "Give me the phone number of customer 5",
            and it will be refused. Use Chrome or Edge for voice. The first load
            may take up to a minute.
          </p>
        </div>
      )}
    </section>
  )
}