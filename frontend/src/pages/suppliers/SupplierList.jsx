import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../context/AuthContext.jsx'

const ratingColor = r => r >= 9 ? 'success' : r >= 7 ? 'info' : r >= 4 ? 'warning' : 'danger'

export default function SupplierList() {
  const { user } = useAuth()
  const canManage = ['admin', 'purchaser'].includes(user?.role)
  const [data, setData] = useState({ results: [], count: 0 })
  const [q, setQ] = useState('')
  const [activeOnly, setActiveOnly] = useState('1')
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    axios.get('/api/suppliers/', { params: { q, active: activeOnly, page_size: 50 } })
      .then(r => setData(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [q, activeOnly])

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-building me-2"></i>Поставщики</h1>
        {canManage && (
          <Link to="/suppliers/new" className="btn btn-primary">
            <i className="bi bi-plus-lg me-1"></i> Новый поставщик
          </Link>
        )}
      </div>

      <div className="card mb-3">
        <div className="card-body py-2 d-flex gap-3 align-items-center">
          <div className="input-group flex-grow-1">
            <span className="input-group-text bg-white"><i className="bi bi-search text-muted"></i></span>
            <input className="form-control border-start-0" placeholder="Поиск по названию или ИНН..."
              value={q} onChange={e => setQ(e.target.value)} />
          </div>
          <select className="form-select" style={{ width: 160 }} value={activeOnly}
            onChange={e => setActiveOnly(e.target.value)}>
            <option value="1">Только активные</option>
            <option value="0">Все</option>
          </select>
        </div>
      </div>

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="spinner-center"><div className="spinner-border text-primary" /></div>
          ) : data.results.length === 0 ? (
            <div className="text-center text-muted py-5">
              <i className="bi bi-building display-4 d-block mb-2"></i>Поставщики не найдены
            </div>
          ) : (
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Наименование</th>
                  <th>ИНН</th>
                  <th>Контакт</th>
                  <th className="text-center">Рейтинг</th>
                  <th className="text-center">Надёжность</th>
                  <th className="text-center">КП</th>
                  <th className="text-center">Заказов</th>
                  <th className="text-center">Статус</th>
                  {canManage && <th className="text-end pe-3">Действия</th>}
                </tr>
              </thead>
              <tbody>
                {data.results.map(s => (
                  <tr key={s.id}>
                    <td className="ps-3">
                      <Link to={`/suppliers/${s.id}`} className="fw-semibold text-decoration-none">{s.name}</Link>
                    </td>
                    <td className="small text-muted">{s.inn}</td>
                    <td className="small">{s.contact_person || '—'}</td>
                    <td className="text-center">
                      <span className={`badge bg-${ratingColor(s.rating)}`}>{s.rating}</span>
                    </td>
                    <td className="text-center small">{s.delivery_reliability}%</td>
                    <td className="text-center small">{s.quotes_count}</td>
                    <td className="text-center small">{s.orders_count}</td>
                    <td className="text-center">
                      <span className={`badge bg-${s.is_active ? 'success' : 'secondary'}`}>
                        {s.is_active ? 'Активен' : 'Неактивен'}
                      </span>
                    </td>
                    {canManage && (
                      <td className="text-end pe-3">
                        <Link to={`/suppliers/${s.id}/edit`} className="btn btn-sm btn-outline-secondary">
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
