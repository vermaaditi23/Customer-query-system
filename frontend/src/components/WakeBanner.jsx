import { useEffect, useState } from 'react'
import { checkHealth } from '../api.js'

export default function WakeBanner() {
  const [waking, setWaking] = useState(false)

  useEffect(() => {
    let cancelled = false
    const timer = setTimeout(() => { if (!cancelled) setWaking(true) }, 2000)

    async function ping() {
      while (!cancelled) {
        try {
          await checkHealth()
          break
        } catch {
          await new Promise((r) => setTimeout(r, 3000))
        }
      }
      clearTimeout(timer)
      if (!cancelled) setWaking(false)
    }
    ping()

    return () => { cancelled = true; clearTimeout(timer) }
  }, [])

  if (!waking) return null
  return (
    <div className="wake-banner" role="status">
      Waking up the assistant, this can take up to a minute...
    </div>
  )
}