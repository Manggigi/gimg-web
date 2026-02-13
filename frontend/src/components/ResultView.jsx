export default function ResultView({ result, onReset }) {
  const filename = result.filename || 'result.png'

  const download = async () => {
    if (!result.blob) return

    // Mobile: use Web Share API (works reliably on iOS Safari + Android)
    if (navigator.share && navigator.canShare) {
      try {
        const file = new File([result.blob], filename, { type: result.blob.type })
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({ files: [file], title: filename })
          return
        }
      } catch (err) {
        // User cancelled or share failed — fall through to anchor method
        if (err.name === 'AbortError') return
      }
    }

    // Desktop / fallback: programmatic anchor click
    const url = URL.createObjectURL(result.blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    setTimeout(() => {
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }, 1000)
  }

  return (
    <div className="result-section">
      {result.type === 'json' ? (
        <div className="result-json">{JSON.stringify(result.data, null, 2)}</div>
      ) : (
        <>
          <img src={result.url} alt="Result" className="result-img" />
          <button
            className="btn-download"
            onClick={download}
          >⬇️ Download Result</button>
        </>
      )}
      <button className="btn-secondary" onClick={onReset}>Process Another Image</button>
    </div>
  )
}
