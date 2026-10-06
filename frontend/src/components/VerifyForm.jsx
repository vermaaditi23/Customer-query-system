
import { verify } from '../api.js'
import { useEffect, useState } from 'react'

export default function VerifyForm({ onVerified, notice, prefill }) {
  const [customerId, setCustomerId] = useState(prefill?.customer_id || '')
  const [orderId, setOrderId] = useState(prefill?.order_id || '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
    useEffect(() => {
    if (prefill) {
      setCustomerId(prefill.customer_id)
      setOrderId(prefill.order_id)
    }
  }, [prefill])

  async function submit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const data = await verify(customerId.trim().toUpperCase(), orderId.trim().toUpperCase())
      onVerified(data.token, data.first_name)
    } catch (err) {
      if (err.status === 429 || err.status === 423) {
        setError('Too many attempts. Please wait a few minutes and try again.')
      } else if (err.status === 401) {
        setError('We could not verify those details.')
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>Verify your account</h2>
      <p className="muted">Enter your customer ID and one of your order IDs.</p>
      {notice && <p className="notice">{notice}</p>}

      <label htmlFor="cid">Customer ID</label>
      <input id="cid" value={customerId} placeholder="CUST0005"
             onChange={(e) => setCustomerId(e.target.value)} required />

      <label htmlFor="oid">Order ID</label>
      <input id="oid" value={orderId} placeholder="ORD00002"
             onChange={(e) => setOrderId(e.target.value)} required />

      {error && <p className="error" role="alert">{error}</p>}

      <button type="submit" disabled={busy}>
        {busy ? 'Verifying...' : 'Verify'}
      </button>
    </form>
  )
}