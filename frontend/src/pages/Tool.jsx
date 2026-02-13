import { useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { tools } from '../data/tools'
import UploadZone from '../components/UploadZone'
import ToolOptions from '../components/ToolOptions'
import ResultView from '../components/ResultView'
import { processImage } from '../api/client'

export default function Tool() {
  const { toolName } = useParams()
  const tool = tools.find(t => t.id === toolName)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [options, setOptions] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const handleFile = (f) => {
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setError(null)
  }

  const reset = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
    setOptions({})
  }

  const handleProcess = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      // Clean options: remove internal keys (prefixed with _) and empty values
      const cleanOpts = {}
      Object.entries(options).forEach(([k, v]) => {
        if (!k.startsWith('_') && v !== '' && v !== undefined && v !== null && v !== false) {
          cleanOpts[k] = v
        }
      })
      const res = await processImage(toolName, file, cleanOpts)
      setResult(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (!tool) return <div className="tool-page"><h1>Tool not found</h1><Link to="/">← Back to tools</Link></div>

  return (
    <div className="tool-page">
      <Link to="/" style={{ color: 'var(--accent)', fontSize: '0.9rem', marginBottom: 16, display: 'inline-block' }}>← All Tools</Link>
      <h1>{tool.icon} {tool.title}</h1>
      <p className="desc">{tool.description}</p>

      {result ? (
        <ResultView result={result} onReset={reset} />
      ) : loading ? (
        <div className="loading-overlay">
          <span className="spinner" />
          <p>Processing your image...</p>
        </div>
      ) : (
        <>
          {!file ? (
            <UploadZone onFile={handleFile} />
          ) : (
            <div className="preview-section">
              <img src={preview} alt="Preview" className="preview-img" />
              <button className="btn-secondary" onClick={reset} style={{ marginBottom: 8, marginTop: 0 }}>Change Image</button>
            </div>
          )}

          {file && <ToolOptions toolId={toolName} options={options} onChange={setOptions} />}

          {file && (
            <button className="btn-process" onClick={handleProcess} disabled={loading}>
              Process Image
            </button>
          )}

          {error && <div className="error-msg">❌ {error}</div>}
        </>
      )}
    </div>
  )
}
