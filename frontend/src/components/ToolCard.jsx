import { useNavigate } from 'react-router-dom'

export default function ToolCard({ tool }) {
  const navigate = useNavigate()
  return (
    <div className="tool-card" onClick={() => navigate(`/tool/${tool.id}`)}>
      <div className="icon">{tool.icon}</div>
      <h3>{tool.title}</h3>
      <p>{tool.description}</p>
    </div>
  )
}
