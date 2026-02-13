export default function ResultView({ result, onReset }) {
  const download = () => {
    if (!result.blob) return
    const url = URL.createObjectURL(result.blob)
    const a = document.createElement('a')
    a.href = url
    a.download = result.filename || 'result.png'
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    // Clean up after a short delay to ensure download starts
    setTimeout(() => {
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }, 500)
  }

  return (
    <div className="result-section">
      {result.type === 'json' ? (
        <div className="result-json">{JSON.stringify(result.data, null, 2)}</div>
      ) : (
        <>
          <img src={result.url} alt="Result" className="result-img" />
          <a
            href={result.url}
            download={result.filename || 'result.png'}
            className="btn-download"
            onClick={(e) => {
              // For browsers that don't support download attr on blob URLs
              // fall back to manual approach
              if (result.blob) {
                e.preventDefault()
                download()
              }
            }}
          >⬇️ Download Result</a>
        </>
      )}
      <button className="btn-secondary" onClick={onReset}>Process Another Image</button>
    </div>
  )
}
