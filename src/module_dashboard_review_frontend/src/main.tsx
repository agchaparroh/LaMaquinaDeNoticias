import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './App.css'  // ✅ Activar estilos globales elegantes

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)