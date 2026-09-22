import { useEffect, useState } from 'react'
import useStore from './store'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import SettingsModal from './components/SettingsModal'
import DockerTerminal from './components/DockerTerminal'
import MatrixRain from './components/MatrixRain'
import WorldPanel from './components/WorldPanel'
import AccountBar from './components/AccountBar'
import { Globe2, ShieldCheck, Users, TerminalSquare } from 'lucide-react'

function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [worldOpen, setWorldOpen] = useState(false)
  const { loadSettings, fetchConversations, fetchProviders, teamMode, terminalCount, removeTerminal, sidebarOpen, toggleSidebar } = useStore()
  const clerkEnabled = Boolean(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY)

  useEffect(() => {
    loadSettings()
    fetchConversations()
    fetchProviders()
  }, [])

  useEffect(() => {
    if (window.innerWidth <= 700 && sidebarOpen) toggleSidebar()
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-team', teamMode)
  }, [teamMode])

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)', color: 'var(--t1)', fontFamily: 'var(--font-mono)', overflow: 'hidden' }}>
      <Sidebar onOpenSettings={() => setSettingsOpen(true)} />

      {/* Main area — matrix rain only here, not in sidebar */}
      <div style={{ flex: 1, display: 'flex', minWidth: 0, position: 'relative' }}>
        <MatrixRain />
        <div className="ramibus-main">
          <header className="ramibus-topbar">
            <div className="ramibus-identity">
              <img src="/ramibus-logo.png" alt="RAMIBUS" />
              <div><strong>RAMIBUS</strong><span>AGENT FABRIC // CONTROL PLANE</span></div>
            </div>
            <div className="ramibus-capabilities" aria-label="RAMIBUS capabilities">
              <span><Users size={12} /> <b>1,200</b> ROLE SLOTS</span>
              <span><ShieldCheck size={12} /> R1 PLANNER</span>
              <span><TerminalSquare size={12} /> REPLIT SHELL</span>
            </div>
            <div className="ramibus-actions">
              <button className={`topbar-button ${worldOpen ? 'active' : ''}`} onClick={() => setWorldOpen((open) => !open)}><Globe2 size={13} /> WORLD</button>
              {clerkEnabled && <AccountBar />}
            </div>
          </header>
          <div className="ramibus-workspace">
            {/* Chat panel */}
            <div className="ramibus-chat-zone" style={{
              display: 'flex', flexDirection: 'column', minWidth: 0,
              flex: terminalCount === 0 ? '1' : '0 0 60%',
              position: 'relative', zIndex: 1,
            }}>
              <ChatPanel />
            </div>

            {/* Terminal zone — no background so matrix shows through */}
            {terminalCount >= 1 && (
              <div className="ramibus-terminal-zone" style={{
                flex: '0 0 40%', display: 'flex', flexDirection: 'column',
                padding: '0.75rem', gap: '0.75rem', boxSizing: 'border-box',
                position: 'relative', zIndex: 1,
              }}>
                <div style={{ flex: 1, minHeight: 0 }}>
                  <DockerTerminal terminalId={1} onClose={() => removeTerminal()} />
                </div>
                {terminalCount >= 2 && (
                  <div style={{ flex: 1, minHeight: 0 }}>
                    <DockerTerminal terminalId={2} onClose={() => removeTerminal()} />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        {worldOpen && <WorldPanel onClose={() => setWorldOpen(false)} />}
      </div>

      {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}
    </div>
  )
}

export default App
