import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

const STATUS_LABELS = {
  draft:'Черновик', submitted:'На рассмотрении', approved:'Утверждена',
  rejected:'Отклонена', ordered:'Заказ размещён', completed:'Исполнена',
}
const STATUS_COLORS = {
  draft:'secondary', submitted:'primary', approved:'success',
  rejected:'danger', ordered:'info', completed:'dark',
}

export default function RequestList() {
  const { user } = useAuth()
  const [data, setData] = useState({ results: [], count: 0 })
  const [q, setQ] = useState('')
  const [statusF, setStatusF] = useState('')
  const [critF, setCritF] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)

  const load = (p = page) => {
    setLoading(true)
    axios.get('/api/requests/', { params: { q, status: statusF, criticality: critF, page: p } })
      .then(r => setData(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load(1); setPage(1) }, [q, statusF, critF])

  const totalPages = Math.ceil(data.count / 20)

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-file-earmark-text me-2"></i>Заявки на закупку</h1>
        <Link to="/requests/new" className="btn btn-primary">
          <i className="bi bi-plus-lg me-1"></i> Новая заявка
        </Link>
      </div>

      <div className="card mb-3">
        <div className="card-body py-2">
          <div className="row g-2">
            <div className="col-md-4">
              <div className="input-group">
                <span className="input-group-text bg-white"><i className="bi bi-search text-muted"></i></span>
                <input className="form-control border-start-0" placeholder="Номер или подразделение..."
                  value={q} onChange={e => setQ(e.target.value)} />
              </div>
            </div>
            <div className="col-md-4">
              <select className="form-select" value={statusF} onChange={e => setStatusF(e.target.value)}>
                <option value="">Все статусы</option>
                {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div className="col-md-4">
              <select className="form-select" value={critF} onChange={e => setCritF(e.target.value)}>
                <option value="">Все типы</option>
                <option value="planned">Плановая</option>
                <option value="emergency">Аварийная</option>
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
              <i className="bi bi-inbox display-4 d-block mb-2"></i>Заявок нет
            </div>
          ) : (
            <>
              <table className="table table-hover mb-0">
                <thead className="table-light">
                  <tr>
                    <th className="ps-3">Номер</th>
                    <th>Подразделение</th>
                    <th className="text-center">Тип</th>
                    <th className="text-center">Статус</th>
                    <th className="text-center">Позиций</th>
                    <th>Дата нужды</th>
                    <th className="text-end pe-3">Сумма, ₽</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map(r => (
                    <tr key={r.id}>
                      <td className="ps-3">
                        <Link to={`/requests/${r.id}`} className="fw-semibold text-decoration-none">
                          {r.request_number}
                        </Link>
                        {r.criticality === 'emergency' && (
                          <span className="badge bg-danger ms-1 small">Аварийная</span>
                        )}
                      </td>
                      <td className="small text-muted">{r.department}</td>
                      <td className="text-center">
                        <span className={`badge bg-${r.criticality === 'emergency' ? 'danger' : 'secondary'}`}>
                          {r.criticality === 'emergency' ? 'Аварийная' : 'Плановая'}
                        </span>
                      </td>
                      <td className="text-center">
                        <span className={`badge bg-${STATUS_COLORS[r.status] || 'secondary'}`}>
                          {STATUS_LABELS[r.status] || r.status}
                        </span>
                      </td>
                      <td className="text-center small">{r.items_count}</td>
                      <td className="small">{r.need_date}</td>
                      <td className="text-end pe-3 small">
                        {r.total_target_amount > 0 ? Number(r.total_target_amount).toLocaleString('ru') : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {totalPages > 1 && (
                <div className="d-flex justify-content-center py-3 gap-2">
                  <button className="btn btn-sm btn-outline-secondary" disabled={page <= 1}
                    onClick={() => { const p = page - 1; setPage(p); load(p) }}>
                    <i className="bi bi-chevron-left"></i>
                  </button>
                  <span className="btn btn-sm disabled">{page} / {totalPages}</span>
                  <button className="btn btn-sm btn-outline-secondary" disabled={page >= totalPages}
                    onClick={() => { const p = page + 1; setPage(p); load(p) }}>
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
