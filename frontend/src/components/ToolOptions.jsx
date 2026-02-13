import { useState } from 'react'

export default function ToolOptions({ toolId, options, onChange }) {
  const set = (key, val) => onChange({ ...options, [key]: val })

  switch (toolId) {
    case 'compress':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>Quality <span className="range-value">{options.quality ?? 80}</span></label>
            <input type="range" min="1" max="100" value={options.quality ?? 80} onChange={e => set('quality', +e.target.value)} />
          </div>
        </div>
      )

    case 'resize':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>Mode</label>
            <div className="radio-group">
              {['dimensions', 'percentage', 'max-size'].map(m => (
                <label key={m}><input type="radio" name="resize-mode" checked={(options._mode ?? 'dimensions') === m} onChange={() => set('_mode', m)} /> {m === 'dimensions' ? 'By Dimensions' : m === 'percentage' ? 'By Percentage' : 'Fit Max Size'}</label>
              ))}
            </div>
          </div>
          {(options._mode ?? 'dimensions') === 'dimensions' && (
            <div className="option-row">
              <div className="option-group"><label>Width</label><input type="number" placeholder="Width" value={options.width ?? ''} onChange={e => set('width', e.target.value)} /></div>
              <div className="option-group"><label>Height</label><input type="number" placeholder="Height" value={options.height ?? ''} onChange={e => set('height', e.target.value)} /></div>
            </div>
          )}
          {options._mode === 'percentage' && (
            <div className="option-group"><label>Percentage</label><input type="number" placeholder="e.g. 50" value={options.percentage ?? ''} onChange={e => set('percentage', e.target.value)} /></div>
          )}
          {options._mode === 'max-size' && (
            <div className="option-group"><label>Max Size (KB)</label><input type="number" placeholder="e.g. 500" value={options['max-size'] ?? ''} onChange={e => set('max-size', e.target.value)} /></div>
          )}
        </div>
      )

    case 'crop':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>Aspect Ratio</label>
            <select value={options.aspect ?? 'free'} onChange={e => set('aspect', e.target.value)}>
              <option value="free">Free (custom)</option>
              <option value="1:1">1:1</option>
              <option value="16:9">16:9</option>
              <option value="4:3">4:3</option>
              <option value="3:2">3:2</option>
            </select>
          </div>
          {(options.aspect ?? 'free') === 'free' && (
            <>
              <div className="option-row">
                <div className="option-group"><label>X</label><input type="number" value={options.x ?? ''} onChange={e => set('x', e.target.value)} /></div>
                <div className="option-group"><label>Y</label><input type="number" value={options.y ?? ''} onChange={e => set('y', e.target.value)} /></div>
              </div>
              <div className="option-row">
                <div className="option-group"><label>Width</label><input type="number" value={options.width ?? ''} onChange={e => set('width', e.target.value)} /></div>
                <div className="option-group"><label>Height</label><input type="number" value={options.height ?? ''} onChange={e => set('height', e.target.value)} /></div>
              </div>
            </>
          )}
        </div>
      )

    case 'rotate':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>Degrees <span className="range-value">{options.degrees ?? 0}°</span></label>
            <input type="range" min="-360" max="360" value={options.degrees ?? 0} onChange={e => set('degrees', +e.target.value)} />
          </div>
          <label className="checkbox-label">
            <input type="checkbox" checked={!!options['auto-orient']} onChange={e => set('auto-orient', e.target.checked)} />
            Auto-orient (fix EXIF rotation)
          </label>
        </div>
      )

    case 'convert':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>Output Format</label>
            <select value={options.format ?? 'png'} onChange={e => set('format', e.target.value)}>
              {['jpg', 'png', 'webp', 'gif', 'bmp', 'tiff'].map(f => <option key={f} value={f}>{f.toUpperCase()}</option>)}
            </select>
          </div>
        </div>
      )

    case 'metadata':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>Action</label>
            <div className="radio-group">
              <label><input type="radio" name="meta-action" checked={(options.action ?? 'view') === 'view'} onChange={() => set('action', 'view')} /> View Metadata</label>
              <label><input type="radio" name="meta-action" checked={options.action === 'strip'} onChange={() => set('action', 'strip')} /> Strip Metadata</label>
            </div>
          </div>
        </div>
      )

    case 'info':
      return null

    case 'watermark':
      return (
        <div className="options-panel">
          <div className="option-group"><label>Text</label><input type="text" placeholder="Watermark text" value={options.text ?? ''} onChange={e => set('text', e.target.value)} /></div>
          <div className="option-row">
            <div className="option-group">
              <label>Position</label>
              <select value={options.position ?? 'center'} onChange={e => set('position', e.target.value)}>
                {['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'top', 'bottom'].map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="option-group">
              <label>Opacity <span className="range-value">{options.opacity ?? 0.5}</span></label>
              <input type="range" min="0" max="1" step="0.05" value={options.opacity ?? 0.5} onChange={e => set('opacity', +e.target.value)} />
            </div>
          </div>
          <div className="option-row">
            <div className="option-group"><label>Font Size</label><input type="number" value={options['font-size'] ?? 24} onChange={e => set('font-size', e.target.value)} /></div>
            <div className="option-group"><label>Color</label><input type="color" value={options.color ?? '#ffffff'} onChange={e => set('color', e.target.value)} /></div>
          </div>
          <label className="checkbox-label">
            <input type="checkbox" checked={!!options.tile} onChange={e => set('tile', e.target.checked)} />
            Tile watermark
          </label>
        </div>
      )

    case 'blur-face':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>Blur Strength <span className="range-value">{options.strength ?? 25}</span></label>
            <input type="range" min="5" max="99" value={options.strength ?? 25} onChange={e => set('strength', +e.target.value)} />
          </div>
        </div>
      )

    case 'remove-bg':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>AI Model</label>
            <select value={options.model ?? 'u2net'} onChange={e => set('model', e.target.value)}>
              <option value="u2net">U2Net (best quality)</option>
              <option value="u2netp">U2NetP (faster)</option>
              <option value="isnet-general-use">ISNet General</option>
            </select>
          </div>
        </div>
      )

    case 'upscale':
      return (
        <div className="options-panel">
          <div className="option-group">
            <label>Scale</label>
            <div className="radio-group">
              <label><input type="radio" name="scale" checked={(options.scale ?? '2') === '2'} onChange={() => set('scale', '2')} /> 2x</label>
              <label><input type="radio" name="scale" checked={options.scale === '4'} onChange={() => set('scale', '4')} /> 4x</label>
            </div>
          </div>
          <label className="checkbox-label">
            <input type="checkbox" checked={!!options.sharpen} onChange={e => set('sharpen', e.target.checked)} />
            Apply sharpening
          </label>
        </div>
      )

    case 'meme':
      return (
        <div className="options-panel">
          <div className="option-group"><label>Top Text</label><input type="text" placeholder="TOP TEXT" value={options['top-text'] ?? ''} onChange={e => set('top-text', e.target.value)} /></div>
          <div className="option-group"><label>Bottom Text</label><input type="text" placeholder="BOTTOM TEXT" value={options['bottom-text'] ?? ''} onChange={e => set('bottom-text', e.target.value)} /></div>
        </div>
      )

    case 'edit':
      return (
        <div className="options-panel">
          <div className="option-row">
            <div className="option-group"><label>Brightness <span className="range-value">{options.brightness ?? 1.0}</span></label><input type="range" min="0" max="3" step="0.1" value={options.brightness ?? 1.0} onChange={e => set('brightness', +e.target.value)} /></div>
            <div className="option-group"><label>Contrast <span className="range-value">{options.contrast ?? 1.0}</span></label><input type="range" min="0" max="3" step="0.1" value={options.contrast ?? 1.0} onChange={e => set('contrast', +e.target.value)} /></div>
          </div>
          <div className="option-row">
            <div className="option-group"><label>Saturation <span className="range-value">{options.saturation ?? 1.0}</span></label><input type="range" min="0" max="3" step="0.1" value={options.saturation ?? 1.0} onChange={e => set('saturation', +e.target.value)} /></div>
            <div className="option-group"><label>Sharpness <span className="range-value">{options.sharpness ?? 1.0}</span></label><input type="range" min="0" max="3" step="0.1" value={options.sharpness ?? 1.0} onChange={e => set('sharpness', +e.target.value)} /></div>
          </div>
          <div className="option-row">
            <div className="option-group">
              <label>Filter</label>
              <select value={options.filter ?? 'none'} onChange={e => set('filter', e.target.value)}>
                {['none', 'grayscale', 'sepia', 'blur', 'sharpen', 'edge', 'emboss', 'invert'].map(f => <option key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</option>)}
              </select>
            </div>
            <div className="option-group">
              <label>Frame</label>
              <select value={options.frame ?? 'none'} onChange={e => set('frame', e.target.value)}>
                {['none', 'polaroid', 'rounded', 'shadow'].map(f => <option key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="option-row">
            <div className="option-group"><label>Border Width</label><input type="number" value={options['border-width'] ?? 0} onChange={e => set('border-width', e.target.value)} /></div>
            <div className="option-group"><label>Border Color</label><input type="color" value={options['border-color'] ?? '#000000'} onChange={e => set('border-color', e.target.value)} /></div>
          </div>
          <div className="option-row">
            <div className="option-group">
              <label>Flip</label>
              <select value={options.flip ?? 'none'} onChange={e => set('flip', e.target.value)}>
                {['none', 'horizontal', 'vertical', 'both'].map(f => <option key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</option>)}
              </select>
            </div>
            <div className="option-group"><label>Thumbnail Size</label><input type="number" placeholder="Optional" value={options.thumbnail ?? ''} onChange={e => set('thumbnail', e.target.value)} /></div>
          </div>
          <label className="checkbox-label">
            <input type="checkbox" checked={!!options['auto-enhance']} onChange={e => set('auto-enhance', e.target.checked)} />
            Auto-enhance
          </label>
        </div>
      )

    default:
      return null
  }
}
