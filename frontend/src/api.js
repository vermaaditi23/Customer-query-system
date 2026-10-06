async function request(path, options = {}) {
  const { headers, ...rest } = options
  const res = await fetch(path, {
    ...rest,
    headers: { 'Content-Type': 'application/json', ...(headers || {}) },
  })
  let data = null
  try { data = await res.json() } catch { /* empty body */ }
  if (!res.ok) {
    const err = new Error('Request failed')
    err.status = res.status
    throw err
  }
  return data
}


export const checkHealth = () => request('/health')

export const verify = (customer_id, order_id) =>
  request('/api/verify', {
    method: 'POST',
    body: JSON.stringify({ customer_id, order_id }),
  })

export const sendChat = (message, token) =>
  request('/api/chat', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ message }),
  })

export const logout = (token) =>
  request('/api/logout', {
    method: 'POST',
    body: JSON.stringify({ token }),
  }).catch(() => null)

export const getSamples = () => request('/api/samples')