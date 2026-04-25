import { useEffect, useState } from 'react'
import axios from 'axios'

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')

  const load = (p = 1, q = '') => {
    setLoading(true)
    axios.get('/api/admin/audit/', { params: { page: p, search: q } })
      .then(r => {
        setLogs(r.data.results || r.data)
        setTotal(r.data.count || 0)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(page, search) }, [page])

  const handleSearch = e => {
    e.preventDefault()
    setPage(1)
    load(1, search)
  }

  const pageSize = 20
  const totalPages = Math.ceil(total / pageSize)

  const ACTION_COLORS = {
    create: 'success',
    update: 'primary',
    delete: 'danger',
    submit: 'warning',
    approve: 'success',
    reject: 'danger',
    status_change: 'info',
  }

  return (
    <div>
      <h1 className="page-title mb-4"><i className="bi bi-journal-text me-2"></i>Журнал операций</h1>

      <div className="card mb-3">
        <div className="card-body py-2">
          <form onSubmit={handleSearch} className="d-flex gap-2">
            <input className="form-control form-control-sm" style={{ maxWidth: 380 }}
              placeholder="Поиск по пользователю или описанию..."
              value={search} onChange={e => setSearch(e.target.value)} />
            <button type="submit" className="btn btn-sm btn-outline-primary">
              <i className="bi bi-search"></i>
            </button>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="spinner-center py-5"><div className="spinner-border text-primary" /></div>
          ) : (
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3" style={{ width: 160 }}>Время</th>
                  <th style={{ width: 120 }}>Пользователь</th>
                  <th style={{ width: 110 }}>Действие</th>
                  <th>Объект</th>
                  <th className="pe-3">Описание</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 && (
                  <tr><td colSpan={5} className="text-center text-muted py-4">Нет записей</td></tr>
                )}
                {logs.map(log => (
                  <tr key={log.id}>
                    <td className="ps-3 small text-muted" style={{ whiteSpace: 'nowrap' }}>
                      {log.timestamp ? new Date(log.timestamp).toLocaleString('ru', {
                        day: '2-digit', month: '2-digit', year: '2-digit',
                        hour: '2-digit', minute: '2-digit'
                      }) : '—'}
                    </td>
                    <td className="small fw-semibold">{log.user_name || log.user || '—'}</td>
                    <td>
                      <span className={`badge bg-${ACTION_COLORS[log.action] || 'secondary'}`}>
                        {log.action || '—'}
                      </span>
                    </td>
                    <td className="small text-muted">{log.object_type} {log.object_id ? `#${log.object_id}` : ''}</td>
                    <td className="small pe-3">{log.description || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {totalPages > 1 && (
          <div className="card-footer bg-white d-flex justify-content-between align-items-center">
            <span className="small text-muted">Всего: {total}</span>
            <nav>
              <ul className="pagination pagination-sm mb-0">
                <li className={`page-item ${page <= 1 ? 'disabled' : ''}`}>
                  <button className="page-link" onClick={() => setPage(p => Math.max(1, p - 1))}>‹</button>
                </li>
                {[...Array(Math.min(totalPages, 7))].map((_, i) => {
                  const p = i + 1
                  return (
                    <li key={p} className={`page-item ${page === p ? 'active' : ''}`}>
                      <button className="page-link" onClick={() => setPage(p)}>{p}</button>
                    </li>
                  )
                })}
                <li className={`page-item ${page >= totalPages ? 'disabled' : ''}`}>
                  <button className="page-link" onClick={() => setPage(p => Math.min(totalPages, p + 1))}>›</button>
                </li>
              </ul>
            </nav>
          </div>
        )}
      </div>
    </div>
  )
}
