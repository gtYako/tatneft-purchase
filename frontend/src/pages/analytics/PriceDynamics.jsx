import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import axios from 'axios'
import { jsPDF } from 'jspdf'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts'

const LINE_COLORS = ['#1a237e', '#e65100', '#2e7d32', '#6a1b9a', '#00838f', '#ad1457', '#f57f17']
const TREND_ICON = { up: '📈', down: '📉', stable: '➡️' }
const TREND_LABEL = { up: 'Рост', down: 'Снижение', stable: 'Стабильно' }
const RISK_COLOR = { low: 'success', medium: 'warning', high: 'danger' }
const RISK_LABEL = { low: 'Низкий риск', medium: 'Средний риск', high: 'Высокий риск' }

const money = value => value == null ? '—' : Number(value).toLocaleString('ru-RU')
const xmlEscape = value => String(value ?? '').replace(/[<>&'"]/g, ch => ({
  '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;',
}[ch]))
const wrapText = (text, maxChars) => {
  const words = String(text || '').split(/\s+/).filter(Boolean)
  const lines = []
  let line = ''
  words.forEach(word => {
    const next = line ? `${line} ${word}` : word
    if (next.length > maxChars && line) {
      lines.push(line)
      line = word
    } else {
      line = next
    }
  })
  if (line) lines.push(line)
  return lines
}
const svgToPng = (svgText, width, height) => new Promise((resolve, reject) => {
  const img = new Image()
  const blob = new Blob([svgText], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  img.onload = () => {
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)
    ctx.drawImage(img, 0, 0, width, height)
    URL.revokeObjectURL(url)
    resolve(canvas.toDataURL('image/png'))
  }
  img.onerror = reject
  img.src = url
})

function AiCard({ materialId, onAiChange }) {
  const [ai, setAi] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const explain = async () => {
    setLoading(true)
    setError('')
    setAi(null)
    onAiChange?.(null)
    try {
      const r = await axios.post('/api/ai/explain-prices/', { material_id: materialId })
      setAi(r.data)
      onAiChange?.(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Ошибка запроса к GigaChat')
      onAiChange?.(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card mt-4">
      <div className="card-header bg-white d-flex align-items-center justify-content-between">
        <div className="fw-semibold">
          <i className="bi bi-stars me-2 text-warning"></i>
          Анализ и прогноз от GigaChat AI
        </div>
        <button className="btn btn-sm btn-primary" onClick={explain} disabled={loading}>
          {loading
            ? <><span className="spinner-border spinner-border-sm me-1" />Анализирую...</>
            : <><i className="bi bi-stars me-1"></i>Объяснить динамику</>}
        </button>
      </div>

      {error && (
        <div className="card-body">
          <div className="alert alert-danger mb-0 py-2">{error}</div>
        </div>
      )}

      {!ai && !loading && !error && (
        <div className="card-body text-muted small">
          Нажмите кнопку: GigaChat проанализирует историю цен и даст прогноз на 1-3 месяца.
        </div>
      )}

      {ai && (
        <div className="card-body">
          <div className="row g-2 mb-3">
            <div className="col-auto">
              <span className="badge bg-secondary fs-6">
                {TREND_ICON[ai.trend]} {TREND_LABEL[ai.trend]}
              </span>
            </div>
            <div className="col-auto">
              <span className={`badge bg-${RISK_COLOR[ai.risk_level]} fs-6`}>
                {RISK_LABEL[ai.risk_level]}
              </span>
            </div>
            <div className="col-auto text-muted small d-flex align-items-center">
              На основе {ai.data_points} точек данных
            </div>
          </div>

          <div className="mb-3">
            <div className="fw-semibold small text-muted mb-1">
              <i className="bi bi-bar-chart me-1"></i>АНАЛИЗ
            </div>
            <p className="mb-0">{ai.analysis}</p>
          </div>

          {ai.forecast && (
            <div className="mb-3 p-3 rounded" style={{ background: '#f0f4ff' }}>
              <div className="fw-semibold small text-primary mb-1">
                <i className="bi bi-graph-up-arrow me-1"></i>ПРОГНОЗ НА 1-3 МЕСЯЦА
              </div>
              <p className="mb-0">{ai.forecast}</p>
            </div>
          )}

          {ai.recommendation && (
            <div className="p-3 rounded" style={{ background: '#f0fff4' }}>
              <div className="fw-semibold small text-success mb-1">
                <i className="bi bi-lightbulb me-1"></i>РЕКОМЕНДАЦИЯ ЗАКУПЩИКУ
              </div>
              <p className="mb-0 fw-semibold">{ai.recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function PriceDynamics() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [apiData, setApiData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [aiReport, setAiReport] = useState(null)
  const [selected, setSelected] = useState(searchParams.get('material') || '')
  const chartRef = useRef(null)

  const load = (matId) => {
    setLoading(true)
    axios.get('/api/analytics/price-dynamics/', { params: { material: matId } })
      .then(r => setApiData(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(selected) }, [])

  const handleSelect = e => {
    const id = e.target.value
    setSelected(id)
    setAiReport(null)
    setSearchParams(id ? { material: id } : {})
    load(id)
  }

  const { price_data = {}, materials = [] } = apiData || {}
  const suppliers = Object.keys(price_data)
  const allDates = new Set()
  suppliers.forEach(s => price_data[s].forEach(p => allDates.add(p.date)))
  const chartData = [...allDates].sort().map(date => {
    const row = { date }
    suppliers.forEach(s => {
      const point = price_data[s].find(p => p.date === date)
      row[s] = point ? point.price : null
    })
    return row
  })
  const supplierRows = suppliers.map((s, i) => {
    const pts = price_data[s]
    const prices = pts.map(p => p.price)
    return {
      supplier: s,
      color: LINE_COLORS[i % LINE_COLORS.length],
      points: pts.length,
      min: Math.min(...prices),
      max: Math.max(...prices),
      last: pts[pts.length - 1]?.price,
    }
  })

  const exportPdf = async () => {
    if (!apiData?.selected_material || !chartData.length) return
    setExporting(true)
    try {
      const chartSvg = chartRef.current?.querySelector('svg')
      const chartSvgText = chartSvg ? new XMLSerializer().serializeToString(chartSvg) : ''
      const chartDataUrl = chartSvgText
        ? `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(chartSvgText)))}`
        : ''

      const width = 1200
      let y = 48
      const parts = []
      const text = (value, x, yy, size = 22, weight = 400, color = '#111827') =>
        parts.push(`<text x="${x}" y="${yy}" font-family="Arial, sans-serif" font-size="${size}" font-weight="${weight}" fill="${color}">${xmlEscape(value)}</text>`)
      const line = (x1, y1, x2, y2, color = '#e5e7eb') =>
        parts.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="1"/>`)

      text('Динамика цен', 48, y, 34, 700)
      y += 34
      text(`${apiData.selected_material.code} — ${apiData.selected_material.name}`, 48, y, 20, 600, '#374151')
      y += 28
      text(`Сформировано: ${new Date().toLocaleString('ru-RU')}`, 48, y, 16, 400, '#6b7280')
      y += 28
      line(48, y, 1152, y)
      y += 28

      text('График цен по поставщикам', 48, y, 24, 700)
      y += 18
      if (chartDataUrl) {
        parts.push(`<image href="${chartDataUrl}" x="48" y="${y}" width="1104" height="360" preserveAspectRatio="xMidYMid meet"/>`)
      } else {
        text('График недоступен для выгрузки', 48, y + 40, 18, 400, '#b91c1c')
      }
      y += 390

      text('Данные по поставщикам', 48, y, 24, 700)
      y += 26
      const cols = [48, 430, 610, 790, 970]
      ;['Поставщик', 'Точек данных', 'Мин. цена, ₽', 'Макс. цена, ₽', 'Последняя цена, ₽'].forEach((h, i) => text(h, cols[i], y, 16, 700))
      y += 16
      line(48, y, 1152, y)
      supplierRows.forEach(row => {
        y += 28
        parts.push(`<circle cx="58" cy="${y - 5}" r="7" fill="${row.color}"/>`)
        text(row.supplier, 76, y, 16, 600)
        text(row.points, cols[1], y, 16)
        text(money(row.min), cols[2], y, 16)
        text(money(row.max), cols[3], y, 16)
        text(money(row.last), cols[4], y, 16, 700)
      })
      y += 34

      if (aiReport) {
        text('Анализ и прогноз от GigaChat AI', 48, y, 24, 700)
        y += 28
        text(`${TREND_LABEL[aiReport.trend] || 'Стабильно'} · ${RISK_LABEL[aiReport.risk_level] || 'Средний риск'} · На основе ${aiReport.data_points || 0} точек данных`, 48, y, 17, 600, '#374151')
        y += 32
        ;[
          ['АНАЛИЗ', aiReport.analysis],
          ['ПРОГНОЗ НА 1-3 МЕСЯЦА', aiReport.forecast],
          ['РЕКОМЕНДАЦИЯ ЗАКУПЩИКУ', aiReport.recommendation],
        ].forEach(([title, body]) => {
          if (!body) return
          text(title, 48, y, 17, 700, '#1f2937')
          y += 24
          wrapText(body, 110).forEach(row => {
            text(row, 48, y, 16, 400, '#374151')
            y += 22
          })
          y += 12
        })
      }

      const height = Math.max(900, y + 48)
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="100%" height="100%" fill="#ffffff"/>${parts.join('')}</svg>`
      const png = await svgToPng(svg, width, height)
      const pdf = new jsPDF('p', 'mm', 'a4')
      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      const imgHeight = pageWidth * height / width
      let remaining = imgHeight
      let position = 0
      pdf.addImage(png, 'PNG', 0, position, pageWidth, imgHeight)
      remaining -= pageHeight
      while (remaining > 0) {
        position -= pageHeight
        pdf.addPage()
        pdf.addImage(png, 'PNG', 0, position, pageWidth, imgHeight)
        remaining -= pageHeight
      }
      pdf.save(`price-dynamics-${apiData.selected_material.code}.pdf`)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-graph-up-arrow me-2"></i>Динамика цен</h1>
        <button className="btn btn-outline-danger" onClick={exportPdf}
          disabled={exporting || loading || !selected || chartData.length === 0}>
          {exporting
            ? <><span className="spinner-border spinner-border-sm me-1" />PDF</>
            : <><i className="bi bi-file-earmark-pdf me-1"></i>Выгрузить PDF</>}
        </button>
      </div>

      <div className="card mb-4">
        <div className="card-body py-2">
          <label className="form-label fw-semibold small mb-1">Выберите материал</label>
          <select className="form-select" value={selected} onChange={handleSelect}
            style={{ maxWidth: 500 }}>
            <option value="">— выберите материал —</option>
            {materials.map(m => (
              <option key={m.id} value={m.id}>{m.code} — {m.name}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div className="spinner-center"><div className="spinner-border text-primary" /></div>}

      {!loading && selected && chartData.length > 0 && (
        <div className="card mb-4">
          <div className="card-header bg-white fw-semibold">
            <i className="bi bi-graph-up me-1 text-primary"></i>
            Цены по поставщикам: {apiData?.selected_material?.code} — {apiData?.selected_material?.name}
          </div>
          <div className="card-body">
            <div ref={chartRef}>
              <ResponsiveContainer width="100%" height={340}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    formatter={(v, name) => [v ? `${Number(v).toLocaleString('ru')} ₽` : '—', name]}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {suppliers.map((s, i) => (
                    <Line key={s} type="monotone" dataKey={s}
                      stroke={LINE_COLORS[i % LINE_COLORS.length]}
                      strokeWidth={2.5} dot={{ r: 3 }} connectNulls />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {!loading && selected && chartData.length > 0 && (
        <div className="card mb-4">
          <div className="card-header bg-white fw-semibold">Данные по поставщикам</div>
          <div className="card-body p-0">
            <table className="table table-sm mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Поставщик</th>
                  <th className="text-center">Точек данных</th>
                  <th className="text-end">Мин. цена, ₽</th>
                  <th className="text-end">Макс. цена, ₽</th>
                  <th className="text-end pe-3">Последняя цена, ₽</th>
                </tr>
              </thead>
              <tbody>
                {supplierRows.map(row => (
                  <tr key={row.supplier}>
                    <td className="ps-3 d-flex align-items-center gap-2">
                      <div style={{ width: 12, height: 12, borderRadius: '50%', background: row.color }} />
                      <span className="fw-semibold small">{row.supplier}</span>
                    </td>
                    <td className="text-center small">{row.points}</td>
                    <td className="text-end small">{money(row.min)}</td>
                    <td className="text-end small">{money(row.max)}</td>
                    <td className="text-end pe-3 small fw-semibold">{money(row.last)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && selected && chartData.length > 0 && (
        <AiCard materialId={selected} onAiChange={setAiReport} />
      )}

      {!loading && selected && chartData.length === 0 && (
        <div className="alert alert-warning">
          <i className="bi bi-exclamation-triangle me-1"></i>
          Нет данных для выбранного материала
        </div>
      )}

      {!selected && !loading && (
        <div className="text-center text-muted py-5">
          <i className="bi bi-graph-up display-4 d-block mb-2"></i>
          Выберите материал для отображения динамики цен
        </div>
      )}
    </div>
  )
}
