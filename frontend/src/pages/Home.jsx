import { useState } from 'react'
import { tools, categories } from '../data/tools'
import ToolCard from '../components/ToolCard'

export default function Home() {
  const [cat, setCat] = useState('All')
  const filtered = cat === 'All' ? tools : tools.filter(t => t.category === cat)

  return (
    <>
      <section className="hero">
        <h1><span>GIMG</span> — Every image tool you need</h1>
        <p>Free. Fast. No uploads to third parties.</p>
      </section>
      <div className="categories">
        {categories.map(c => (
          <button key={c} className={`cat-btn ${cat === c ? 'active' : ''}`} onClick={() => setCat(c)}>{c}</button>
        ))}
      </div>
      <div className="tool-grid">
        {filtered.map(t => <ToolCard key={t.id} tool={t} />)}
      </div>
    </>
  )
}
