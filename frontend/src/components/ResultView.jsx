export default function ResultView({ result, onReset }) {
  const download = () => {
    const a = document.createElement('a')
    a.href = result.url
    a.download = result.filename
    a.click()
  }

  return (
    <div className="result-section">
      {result.type === 'json' ? (
        <div className="result-json">{JSON.stringify(result.data, null, 2)}</div>
      ) : (
        <>
          <img src={result.url} alt="Result" className="result-img" />
          <button className="btn-download" onClick={download}>⬇️ Download Result</button>
        </>
      )}
      <button className="btn-secondary" onClick={onReset}>Process Another Image</button>
    </div>
  )
}
