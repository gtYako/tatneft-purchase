import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

export default function StockList() {
  const { user } = useAuth()
  const canManage = ['admin', 'purchaser', 'analyst'].includes(user?.role)
  const [data, setData] = useState({ results: [], count: 0, low_count: 0 })
  const [q, setQ] = useState('')
  const [showLow, setShowLow] = useState(false)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)

  const load = () => {
    setLoading(true)
    axios.get('/api/warehouse/', { params: { q, low: showLow ? '1' : '', page_size: 50 } })
      .then(r => setData(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [q, showLow])

  const handleDelete = async id => {
    if (!window.confirm('Удалить запись склада?')) return
    setDeleting(id)
    await axios.delete(`/api/warehouse/${id}/`).catch(() => {})
    setDeleting(null)
    load()
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="page-title mb-0"><i className="bi bi-archive me-2"></i>Складские остатки</h1>
          {data.low_count > 0 && (
            <span className="badge bg-danger mt-1">{data.low_count} позиций ниже минимума</span>
          )}
        </div>
        {canManage && (
          <Link to="/warehouse/new" className="btn btn-primary">
            <i className="bi bi-plus-lg me-1"></i> Добавить запись
          </Link>
        )}
      </div>

      <div className="card mb-3">
        <div className="card-body py-2 d-flex gap-3 align-items-center">
          <div className="input-group flex-grow-1">
            <span className="input-group-text bg-white"><i className="bi bi-search text-muted"></i></span>
            <input className="form-control border-start-0" placeholder="Поиск..."
              value={q} onChange={e => setQ(e.target.value)} />
          </div>
          <div className="form-check mb-0">
            <input className="form-check-input" type="checkbox" id="showLow"
              checked={showLow} onChange={e => setShowLow(e.target.checked)} />
            <label className="form-check-label text-danger small" htmlFor="showLow">
              <i className="bi bi-exclamation-triangle me-1"></i>Только дефицит
            </label>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="spinner-center"><div className="spinner-border text-primary" /></div>
          ) : data.results.length === 0 ? (
            <div className="text-center text-muted py-5">
              <i className="bi bi-inbox display-4 d-block mb-2"></i>Данных нет
            </div>
          ) : (
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Код</th>
                  <th>Материал</th>
                  <th>Место хранения</th>
                  <th className="text-center">На складе</th>
                  <th className="text-center">Резерв</th>
                  <th className="text-center">Доступно</th>
                  <th className="text-center">Мин. запас</th>
                  <th className="text-center">Статус</th>
                  {canManage && <th className="text-end pe-3">Действия</th>}
                </tr>
              </thead>
              <tbody>
                {data.results.map(s => (
                  <tr key={s.id} className={s.is_low ? 'table-warning' : ''}>
                    <td className="ps-3"><code className="text-primary small">{s.material_code}</code></td>
                    <td>
                      <Link to={`/catalog/${s.material}`} className="text-decoration-none small fw-semibold">
                        {s.material_name?.substring(0, 45)}{s.material_name?.length > 45 ? '…' : ''}
                      </Link>
                    </td>
                    <td className="small text-muted">{s.location}</td>
                    <td className="text-center small">{parseFloat(s.qty_on_hand).toFixed(1)} {s.material_unit}</td>
                    <td className="text-center small text-warning">{parseFloat(s.qty_reserved).toFixed(1)}</td>
                    <td className="text-center small fw-semibold">{parseFloat(s.qty_available).toFixed(1)}</td>
                    <td className="text-center small">{parseFloat(s.material_min_stock).toFixed(1)}</td>
                    <td className="text-center">
                      <span className={`badge bg-${s.is_low ? 'danger' : 'success'}`}>
                        {s.is_low ? 'Дефицит' : 'Норма'}
                      </span>
                    </td>
                    {canManage && (
                      <td className="text-end pe-3">
                        <Link to={`/warehouse/${s.id}/edit`} className="btn btn-sm btn-outline-secondary me-1">
                          <i className="bi bi-pencil"></i>
                        </Link>
                        <button className="btn btn-sm btn-outline-danger" disabled={deleting === s.id}
                          onClick={() => handleDelete(s.id)}>
                          <i className="bi bi-trash"></i>
                        </button>
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
