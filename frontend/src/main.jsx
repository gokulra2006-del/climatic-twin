import React, { Component } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { AuthProvider } from './context/AuthContext.jsx'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', backgroundColor: '#0f172a', color: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', fontFamily: 'system-ui, sans-serif' }}>
          <div style={{ maxWidth: '600px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)' }}>
            <h2 style={{ color: '#ef4444', fontSize: '20px', fontWeight: 'bold', marginBottom: '12px' }}>⚠️ Dashboard Render Notice</h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '16px' }}>An error occurred while rendering the UI component:</p>
            <pre style={{ backgroundColor: '#0f172a', padding: '12px', borderRadius: '8px', color: '#fca5a5', fontSize: '12px', overflowX: 'auto', marginBottom: '20px' }}>
              {this.state.error?.toString() || 'Unknown rendering exception'}
            </pre>
            <button
              onClick={() => {
                localStorage.clear()
                window.location.reload()
              }}
              style={{ backgroundColor: '#4f46e5', color: '#ffffff', padding: '10px 20px', borderRadius: '8px', border: 'none', fontWeight: 'bold', cursor: 'pointer' }}
            >
              Reset Session &amp; Reload Dashboard
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)

