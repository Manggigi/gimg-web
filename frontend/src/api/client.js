const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8787'

export async function processImage(toolName, file, options = {}) {
  const formData = new FormData()
  formData.append('file', file)
  Object.entries(options).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      formData.append(key, value)
    }
  })

  const res = await fetch(`${API_URL}/api/${toolName}`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Error ${res.status}`)
  }

  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return { type: 'json', data: await res.json() }
  }

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const filename = res.headers.get('content-disposition')?.match(/filename="?(.+?)"?$/)?.[1] || `result.${blob.type.split('/')[1] || 'png'}`
  return { type: 'image', url, blob, filename }
}
