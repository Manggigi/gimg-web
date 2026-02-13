import { useRef, useState } from 'react'

export default function UploadZone({ onFile }) {
  const inputRef = useRef()
  const [dragOver, setDragOver] = useState(false)

  const handleFile = (file) => {
    if (file && file.type.startsWith('image/')) onFile(file)
  }

  return (
    <div
      className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]) }}
    >
      <div className="upload-icon">📁</div>
      <p>Drop image here or click to upload</p>
      <p className="hint">Supports JPG, PNG, WEBP, GIF, BMP, TIFF</p>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => handleFile(e.target.files[0])}
      />
    </div>
  )
}
