import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

export default function QuoteList() {
  const { user } = useAuth()
  const canManage = ['admin', 'purchaser'].includes(user?.role)
  const [data, setData] = useState({ results: [], count: 0 })
  const [q, setQ] = useState('')
  const [matId, setMatId] = useState('')
  const [supId, setSupId] = useState('')
  const [materials, setMaterials] = useState([])
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)

  const load = () => {
    setLoading(true)
    axios.get('/api/quotes/', { params: { q, material: matId, supplier: supId, page_size: 50 } })
      .then(r => {
        setData(r.data)
        setMaterials(r.data.materials || [])
        setSuppliers(r.data.suppliers || [])
      }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [q, matId, supId])

  const handleDelete = async id => {
    if (!window.confirm('Удалить ценовое предложение?')) return
    setDeleting(id)
    await axios.delete(`/api/quotes/${id}/`).catch(() => {})
    setDeleting(null)
    load()
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-currency-dollar me-2"></i>Ценовые предложения (КП)</h1>
        {canManage && (
          <Link to="/quotes/new" className="btn btn-primary">
            <i className="bi bi-plus-lg me-1"></i> Новое КП
          </Link>
        )}
      </div>

      <div className="card mb-3">
        <div className="card-body py-2">
          <div className="row g-2">
            <div className="col-md-4">
              <div className="input-group">
                <span className="input-group-text bg-white"><i className="bi bi-search text-muted"></i></span>
                <input className="form-control border-start-0" placeholder="Поиск..."
                  value={q} onChange={e => setQ(e.target.value)} />
              </div>
            </div>
            <div className="col-md-4">
              <select className="form-select" value={matId} onChange={e => setMatId(e.target.value)}>
                <option value="">Все материалы</option>
                {materials.map(m => <option key={m.id} value={m.id}>{m.code} — {m.name?.substring(0, 40)}</option>)}
              </select>
            </div>
            <div className="col-md-4">
              <select className="form-select" value={supId} onChange={e => setSupId(e.target.value)}>
                <option value="">Все поставщики</option>
                {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
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
              <i className="bi bi-inbox display-4 d-block mb-2"></i>КП не найдены
            </div>
          ) : (
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Материал</th>
                  <th>Поставщик</th>
                  <th className="text-end">Цена, ₽</th>
                  <th className="text-center">Срок, дн.</th>
                  <th>Условия оплаты</th>
                  <th>Дата КП</th>
                  <th className="text-center">Актуально</th>
                  {canManage && <th className="text-end pe-3">Действия</th>}
                </tr>
              </thead>
              <tbody>
                {data.results.map(q => (
                  <tr key={q.id}>
                    <td className="ps-3 small">
                      <Link to={`/catalog/${q.material}`} className="fw-semibold text-decoration-none">
                        {q.material_code}
                      </Link>
                      <div className="text-muted" style={{ fontSize: '0.75rem' }}>
                        {q.material_name?.substring(0, 45)}
                      </div>
                    </td>
                    <td className="small fw-semibold">{q.supplier_name}</td>
                    <td className="text-end small">{Number(q.price).toLocaleString('ru')}</td>
                    <td className="text-center small">{q.delivery_days}</td>
                    <td className="small text-muted">{q.payment_terms || '—'}</td>
                    <td className="small">{q.quote_date}</td>
                    <td className="text-center">
                      <span className={`badge bg-${q.is_valid ? 'success' : 'secondary'}`}>
                        {q.is_valid ? 'Да' : 'Истекло'}
                      </span>
                    </td>
                    {canManage && (
                      <td className="text-end pe-3">
                        <Link to={`/quotes/${q.id}/edit`} className="btn btn-sm btn-outline-secondary me-1">
                          <i className="bi bi-pencil"></i>
                        </Link>
                        <button className="btn btn-sm btn-outline-danger" disabled={deleting === q.id}
                          onClick={() => handleDelete(q.id)}>
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
