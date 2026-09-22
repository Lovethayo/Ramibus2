import { useEffect, useState } from 'react'
import { User, X, Save, LogIn, UserPlus } from 'lucide-react'
import { SignInButton, SignUpButton, useUser } from '@clerk/react'

const inputStyle = {
  width: '100%',
  boxSizing: 'border-box',
  background: 'var(--surface-2)',
  border: '1px solid var(--bd)',
  borderRadius: 0,
  color: 'var(--t1)',
  fontFamily: 'var(--font-mono)',
  fontSize: '0.72rem',
  padding: '0.45rem 0.55rem',
  outline: 'none',
}

function AccountBar() {
  const { isLoaded, isSignedIn, user } = useUser()
  const [profileOpen, setProfileOpen] = useState(false)
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState('')

  useEffect(() => {
    if (user) {
      setFirstName(user.firstName || '')
      setLastName(user.lastName || '')
    }
  }, [user])

  if (!isLoaded) return <span className="account-status">AUTH CHECK...</span>

  if (!isSignedIn) {
    return (
      <div className="account-actions">
        <SignInButton mode="modal">
          <button className="account-button"><LogIn size={12} /> SIGN IN</button>
        </SignInButton>
        <SignUpButton mode="modal">
          <button className="account-button account-button-primary"><UserPlus size={12} /> SIGN UP</button>
        </SignUpButton>
      </div>
    )
  }

  const saveProfile = async () => {
    if (!user) return
    setSaving(true)
    setStatus('')
    try {
      await user.update({ firstName: firstName.trim(), lastName: lastName.trim() })
      setStatus('PROFILE UPDATED')
      setTimeout(() => setStatus(''), 2200)
    } catch (error) {
      setStatus(error?.errors?.[0]?.longMessage || 'UPDATE FAILED')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <button
        className="profile-trigger"
        onClick={() => setProfileOpen(true)}
        title="Edit profile"
        aria-label="Edit profile"
      >
        {user.imageUrl ? <img src={user.imageUrl} alt="" /> : <User size={14} />}
        <span>{user.firstName || user.username || 'OPERATOR'}</span>
      </button>

      {profileOpen && (
        <div className="profile-backdrop" onClick={(event) => event.target === event.currentTarget && setProfileOpen(false)}>
          <section className="profile-card" role="dialog" aria-modal="true" aria-label="Edit profile">
            <header className="profile-header">
              <div><span className="profile-kicker">IDENTITY CONSOLE</span><strong>EDIT OPERATOR PROFILE</strong></div>
              <button className="icon-button" onClick={() => setProfileOpen(false)} aria-label="Close profile"><X size={16} /></button>
            </header>
            <div className="profile-body">
              <div className="profile-avatar">{user.imageUrl ? <img src={user.imageUrl} alt="" /> : <User size={28} />}</div>
              <div className="profile-fields">
                <label>FIRST NAME<input value={firstName} onChange={(event) => setFirstName(event.target.value)} style={inputStyle} /></label>
                <label>LAST NAME<input value={lastName} onChange={(event) => setLastName(event.target.value)} style={inputStyle} /></label>
                <div className="profile-readonly">ACCOUNT · {user.primaryEmailAddress?.emailAddress || user.username || 'CLERK IDENTITY'}</div>
              </div>
            </div>
            {status && <div className="profile-status">{status}</div>}
            <footer className="profile-footer">
              <button className="account-button" onClick={() => setProfileOpen(false)}>CLOSE</button>
              <button className="account-button account-button-primary" onClick={saveProfile} disabled={saving}><Save size={12} /> {saving ? 'SAVING...' : 'SAVE PROFILE'}</button>
            </footer>
          </section>
        </div>
      )}
    </>
  )
}

export default AccountBar