import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const CRIT_COLORS = { critical: 'danger', high: 'warning', medium: 'primary', low: 'secondary' }
const CRIT_LABELS = { critical: 'Критическая', high: 'Высокая', medium: 'Средняя', low: 'Низкая' }
const LINE_COLORS = ['#1a237e', '#e65100', '#2e7d32', '#6a1b9a', '#00838f', '#ad1457']

export default function MaterialDetail() {
  const { pk } = useParams()
  const { user } = useAuth()
  const canManage = ['admin', 'purchaser'].includes(user?.role)
  const [mat, setMat] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`/api/materials/${pk}/`).then(r => setMat(r.data)).finally(() => setLoading(false))
  }, [pk])

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>
  if (!mat) return <div className="alert alert-danger">Материал не найден</div>

  // Build chart data from price_history grouped by supplier
  const supplierMap = {}
  const allDates = new Set()
  ;(mat.price_history || []).forEach(p => {
    if (!supplierMap[p.supplier]) supplierMap[p.supplier] = {}
    supplierMap[p.supplier][p.date] = p.price
    allDates.add(p.date)
  })
  const suppliers = Object.keys(supplierMap)
  const chartData = [...allDates].sort().map(date => {
    const row = { date }
    suppliers.forEach(s => { row[s] = supplierMap[s][date] || null })
    return row
  })

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to="/catalog" className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left"></i></Link>
        <div>
          <h1 className="page-title mb-0">{mat.name}</h1>
          <code className="text-primary">{mat.code}</code>
        </div>
        {canManage && (
          <div className="ms-auto d-flex gap-2">
            <Link to={`/catalog/${pk}/edit`} className="btn btn-outline-primary btn-sm">
              <i className="bi bi-pencil me-1"></i> Редактировать
            </Link>
            <Link to={`/quotes/new?material=${pk}`} className="btn btn-success btn-sm">
              <i className="bi bi-plus-lg me-1"></i> Добавить КП
            </Link>
          </div>
        )}
      </div>

      <div className="row g-3 mb-3">
        {/* Info card */}
        <div className="col-lg-4">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">Характеристики</div>
            <div className="card-body">
              <table className="table table-sm table-borderless mb-0">
                <tbody>
                  {[
                    ['Категория', mat.category_name],
                    ['Ед. изм.', mat.unit],
                    ['ГОСТ/ТУ', mat.gost || '—'],
                    ['Критичность', <span className={`badge bg-${CRIT_COLORS[mat.criticality]}`}>{CRIT_LABELS[mat.criticality]}</span>],
                    ['Мин. запас', `${mat.min_stock_level} ${mat.unit}`],
                    ['На складе', `${mat.available_stock?.toFixed(1)} ${mat.unit}`],
                    ['Лучшая цена', mat.best_price ? `${Number(mat.best_price).toLocaleString('ru')} ₽` : '—'],
                  ].map(([k, v]) => (
                    <tr key={k}>
                      <td className="text-muted small pe-3" style={{ whiteSpace: 'nowrap' }}>{k}</td>
                      <td className="fw-semibold small">{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {mat.technical_specs && (
                <div className="mt-2 small text-muted border-top pt-2">
                  <strong>Тех. характеристики:</strong><br />{mat.technical_specs}
                </div>
              )}
              {mat.is_below_min_stock && (
                <div className="alert alert-danger py-2 mt-2 small mb-0">
                  <i className="bi bi-exclamation-triangle-fill me-1"></i>Ниже минимального запаса!
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Stocks */}
        <div className="col-lg-8">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">Складские остатки</div>
            <div className="card-body p-0">
              {mat.stocks?.length === 0 ? (
                <div className="text-center text-muted py-4 small">Нет данных</div>
              ) : (
                <table className="table table-sm table-hover mb-0">
                  <thead className="table-light">
                    <tr><th className="ps-3">Место хранения</th><th>На складе</th><th>Резерв</th><th>Доступно</th></tr>
                  </thead>
                  <tbody>
                    {mat.stocks?.map(s => (
                      <tr key={s.id} className={s.is_low ? 'table-warning' : ''}>
                        <td className="ps-3 small">{s.location}</td>
                        <td className="small">{parseFloat(s.qty_on_hand).toFixed(1)} {mat.unit}</td>
                        <td className="small text-warning">{parseFloat(s.qty_reserved).toFixed(1)}</td>
                        <td className="small fw-semibold">{parseFloat(s.qty_available).toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Price history chart */}
      {chartData.length > 1 && (
        <div className="card mb-3">
          <div className="card-header bg-white fw-semibold">
            <i className="bi bi-graph-up me-1 text-primary"></i> Динамика цен по поставщикам
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                <Tooltip formatter={(v, name) => [`${Number(v).toLocaleString('ru')} ₽`, name]} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {suppliers.map((s, i) => (
                  <Line key={s} type="monotone" dataKey={s} stroke={LINE_COLORS[i % LINE_COLORS.length]}
                    strokeWidth={2} dot={false} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Quotes table */}
      <div className="card">
        <div className="card-header bg-white d-flex justify-content-between align-items-center">
          <span className="fw-semibold"><i className="bi bi-currency-dollar me-1 text-success"></i> Ценовые предложения</span>
          {canManage && (
            <Link to={`/quotes/new?material=${pk}`} className="btn btn-sm btn-success">
              <i className="bi bi-plus-lg me-1"></i> Добавить КП
            </Link>
          )}
        </div>
        <div className="card-body p-0">
          {!mat.quotes?.length ? (
            <div className="text-center text-muted py-4 small">Предложений нет</div>
          ) : (
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Поставщик</th>
                  <th className="text-end">Цена, ₽</th>
                  <th className="text-center">Срок, дн.</th>
                  <th>Условия оплаты</th>
                  <th>Дата КП</th>
                  <th className="text-center">Актуально</th>
                  {canManage && <th></th>}
                </tr>
              </thead>
              <tbody>
                {mat.quotes.map(q => (
                  <tr key={q.id}>
                    <td className="ps-3 small fw-semibold">{q.supplier_name}</td>
                    <td className="text-end small">{Number(q.price).toLocaleString('ru')}</td>
                    <td className="text-center small">{q.delivery_days}</td>
                    <td className="small text-muted">{q.payment_terms || '—'}</td>
                    <td className="small">{q.quote_date}</td>
                    <td className="text-center">
                      <span className={`badge bg-${q.is_valid ? 'success' : 'secondary'}`}>
                        {q.is_valid ? 'Да' : 'Нет'}
                      </span>
                    </td>
                    {canManage && (
                      <td>
                        <Link to={`/quotes/${q.id}/edit`} className="btn btn-sm btn-outline-secondary">
                          <i className="bi bi-pencil"></i>
                        </Link>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
