import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ClerkProvider } from '@clerk/react'

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
const app = publishableKey ? (
  <ClerkProvider publishableKey={publishableKey}>
    <App />
  </ClerkProvider>
) : <App />

createRoot(document.getElementById('root')).render(<StrictMode>{app}</StrictMode>)
