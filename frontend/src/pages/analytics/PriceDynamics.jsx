import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import axios from 'axios'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts'

const LINE_COLORS = ['#1a237e', '#e65100', '#2e7d32', '#6a1b9a', '#00838f', '#ad1457', '#f57f17']

const TREND_ICON = { up: '📈', down: '📉', stable: '➡️' }
const TREND_LABEL = { up: 'Рост', down: 'Снижение', stable: 'Стабильно' }
const RISK_COLOR = { low: 'success', medium: 'warning', high: 'danger' }
const RISK_LABEL = { low: 'Низкий риск', medium: 'Средний риск', high: 'Высокий риск' }

function AiCard({ materialId }) {
  const [ai, setAi] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const explain = async () => {
    setLoading(true)
    setError('')
    setAi(null)
    try {
      const r = await axios.post('/api/ai/explain-prices/', { material_id: materialId })
      setAi(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Ошибка запроса к GPT')
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
            ? <><span className="spinner-border spinner-border-sm me-1" />Анализирую…</>
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
          Нажмите кнопку — GPT проанализирует историю цен и даст прогноз на 1–3 месяца.
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
                <i className="bi bi-graph-up-arrow me-1"></i>ПРОГНОЗ НА 1–3 МЕСЯЦА
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
  const [selected, setSelected] = useState(searchParams.get('material') || '')

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
    setSearchParams(id ? { material: id } : {})
    load(id)
  }

  const { price_data = {}, materials = [] } = apiData || {}
  const suppliers = Object.keys(price_data)

  // Recharts ожидает массив строк по датам, поэтому разворачиваем данные поставщиков в единую таблицу.
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

  return (
    <div>
      <h1 className="page-title mb-4"><i className="bi bi-graph-up-arrow me-2"></i>Динамика цен</h1>

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
            <ResponsiveContainer width="100%" height={340}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
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
                {suppliers.map((s, i) => {
                  const pts = price_data[s]
                  const prices = pts.map(p => p.price)
                  const last = pts[pts.length - 1]?.price
                  return (
                    <tr key={s}>
                      <td className="ps-3 d-flex align-items-center gap-2">
                        <div style={{ width: 12, height: 12, borderRadius: '50%', background: LINE_COLORS[i % LINE_COLORS.length] }} />
                        <span className="fw-semibold small">{s}</span>
                      </td>
                      <td className="text-center small">{pts.length}</td>
                      <td className="text-end small">{Math.min(...prices).toLocaleString('ru')}</td>
                      <td className="text-end small">{Math.max(...prices).toLocaleString('ru')}</td>
                      <td className="text-end pe-3 small fw-semibold">{Number(last).toLocaleString('ru')}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && selected && chartData.length > 0 && (
        <AiCard materialId={selected} />
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
