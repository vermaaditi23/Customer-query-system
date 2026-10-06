import { useState } from 'react'
import WakeBanner from './components/WakeBanner.jsx'
import VerifyForm from './components/VerifyForm.jsx'
import ChatWindow from './components/ChatWindow.jsx'
import { logout } from './api.js'
import SamplePanel from './components/SamplePanel.jsx'

export default function App() {
  const [token, setToken] = useState(sessionStorage.getItem('token') || '')
  const [firstName, setFirstName] = useState(sessionStorage.getItem('firstName') || '')
  const [notice, setNotice] = useState('')
  const [prefill, setPrefill] = useState(null)

  function handleVerified(t, name) {
    sessionStorage.setItem('token', t)
    sessionStorage.setItem('firstName', name || '')
    setToken(t)
    setFirstName(name || '')
    setNotice('')
  }

  function clearSession(message = '') {
    sessionStorage.clear()
    setToken('')
    setFirstName('')
    setNotice(message)
  }

  async function handleLogout() {
    await logout(token)
    clearSession()
  }

  return (
    <div className="app">
      <WakeBanner />
      <header className="top">
        <h1>Customer Support Assistant</h1>
        {token && <button className="link" onClick={handleLogout}>Log out</button>}
      </header>
  
             <main>
        {!token ? (
          <>
            <VerifyForm onVerified={handleVerified} notice={notice} prefill={prefill} />
            <SamplePanel
              onUseCredentials={(c, o) => setPrefill({ customer_id: c, order_id: o })}
            />
          </>
        ) : (
          <ChatWindow
            token={token}
            firstName={firstName}
            onExpired={() => clearSession('Session expired, please verify again.')}
          />
        )}
      </main>
    </div>
  )
}