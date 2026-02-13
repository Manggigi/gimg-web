import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import Tool from './pages/Tool'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <nav className="navbar">
        <Link to="/" className="logo">🖼️ GIMG</Link>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/tool/:toolName" element={<Tool />} />
        </Routes>
      </main>
      <footer className="footer">
        <p>GIMG — Free image tools. No uploads to third parties.</p>
      </footer>
    </div>
  )
}
