import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

const CRIT_LABELS = { critical: 'Критическая', high: 'Высокая', medium: 'Средняя', low: 'Низкая' }
const CRIT_COLORS = { critical: 'danger', high: 'warning', medium: 'primary', low: 'secondary' }

export default function MaterialList() {
  const { user } = useAuth()
  const canManage = ['admin', 'purchaser'].includes(user?.role)
  const [data, setData] = useState({ results: [], count: 0 })
  const [q, setQ] = useState('')
  const [catId, setCatId] = useState('')
  const [crit, setCrit] = useState('')
  const [cats, setCats] = useState([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/categories/all/').then(r => setCats(r.data)).catch(() => {})
  }, [])

  const load = (p = page) => {
    setLoading(true)
    axios.get('/api/materials/', { params: { q, category: catId, criticality: crit, page: p } })
      .then(r => setData(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(1); setPage(1) }, [q, catId, crit])

  const totalPages = Math.ceil(data.count / 20)

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-box-seam me-2"></i>Каталог МТР</h1>
        {canManage && (
          <Link to="/catalog/new" className="btn btn-primary">
            <i className="bi bi-plus-lg me-1"></i> Добавить материал
          </Link>
        )}
      </div>

      <div className="card mb-3">
        <div className="card-body py-2">
          <div className="row g-2">
            <div className="col-md-5">
              <div className="input-group">
                <span className="input-group-text bg-white"><i className="bi bi-search text-muted"></i></span>
                <input className="form-control border-start-0" placeholder="Поиск по коду или наименованию..."
                  value={q} onChange={e => setQ(e.target.value)} />
              </div>
            </div>
            <div className="col-md-4">
              <select className="form-select" value={catId} onChange={e => setCatId(e.target.value)}>
                <option value="">Все категории</option>
                {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="col-md-3">
              <select className="form-select" value={crit} onChange={e => setCrit(e.target.value)}>
                <option value="">Все критичности</option>
                {Object.entries(CRIT_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="spinner-center"><div className="spinner-border text-primary" /></div>
          ) : data.results.length === 0 ? (
            <div className="text-center text-muted py-5">
              <i className="bi bi-inbox display-4 d-block mb-2"></i>Материалы не найдены
            </div>
          ) : (
            <>
              <table className="table table-hover mb-0">
                <thead className="table-light">
                  <tr>
                    <th className="ps-3">Код</th>
                    <th>Наименование</th>
                    <th>Категория</th>
                    <th className="text-center">Ед.</th>
                    <th className="text-center">Критичность</th>
                    <th className="text-center">На складе</th>
                    <th className="text-end">Лучшая цена</th>
                    {canManage && <th className="text-end pe-3">Действия</th>}
                  </tr>
                </thead>
                <tbody>
                  {data.results.map(m => (
                    <tr key={m.id} className={m.is_below_min_stock ? 'table-danger' : ''}>
                      <td className="ps-3">
                        <code className="text-primary">{m.code}</code>
                      </td>
                      <td>
                        <Link to={`/catalog/${m.id}`} className="text-decoration-none fw-semibold small">
                          {m.name.length > 55 ? m.name.substring(0, 55) + '…' : m.name}
                        </Link>
                        {m.is_below_min_stock && (
                          <span className="badge bg-danger ms-1 small">Дефицит</span>
                        )}
                      </td>
                      <td className="text-muted small">{m.category_name}</td>
                      <td className="text-center small">{m.unit}</td>
                      <td className="text-center">
                        <span className={`badge bg-${CRIT_COLORS[m.criticality]}`}>
                          {CRIT_LABELS[m.criticality]}
                        </span>
                      </td>
                      <td className="text-center small">{m.available_stock?.toFixed(0)} {m.unit}</td>
                      <td className="text-end small">
                        {m.best_price != null ? `${Number(m.best_price).toLocaleString('ru')} ₽` : '—'}
                      </td>
                      {canManage && (
                        <td className="text-end pe-3">
                          <Link to={`/catalog/${m.id}/edit`} className="btn btn-sm btn-outline-secondary">
                            <i className="bi bi-pencil"></i>
                          </Link>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
              {totalPages > 1 && (
                <div className="d-flex justify-content-center py-3 gap-2">
                  <button className="btn btn-sm btn-outline-secondary" disabled={page <= 1}
                    onClick={() => { setPage(p => p - 1); load(page - 1) }}>
                    <i className="bi bi-chevron-left"></i>
                  </button>
                  <span className="btn btn-sm disabled">Стр. {page} / {totalPages}</span>
                  <button className="btn btn-sm btn-outline-secondary" disabled={page >= totalPages}
                    onClick={() => { setPage(p => p + 1); load(page + 1) }}>
                    <i className="bi bi-chevron-right"></i>
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
