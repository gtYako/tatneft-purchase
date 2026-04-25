import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

const STATUS_LABELS = { draft:'Черновик', sent:'Отправлен', confirmed:'Подтверждён', delivered:'Доставлен', cancelled:'Отменён' }
const STATUS_COLORS = { draft:'secondary', sent:'primary', confirmed:'info', delivered:'success', cancelled:'danger' }

export default function OrderList() {
  const [data, setData] = useState({ results: [], count: 0 })
  const [q, setQ] = useState('')
  const [statusF, setStatusF] = useState('')
  const [suppliers, setSuppliers] = useState([])
  const [supF, setSupF] = useState('')
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    axios.get('/api/orders/', { params: { q, status: statusF, supplier: supF, page_size: 50 } })
      .then(r => { setData(r.data); setSuppliers(r.data.suppliers_all || []) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [q, statusF, supF])

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-cart3 me-2"></i>Заказы поставщикам</h1>
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
              <select className="form-select" value={statusF} onChange={e => setStatusF(e.target.value)}>
                <option value="">Все статусы</option>
                {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div className="col-md-4">
              <select className="form-select" value={supF} onChange={e => setSupF(e.target.value)}>
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
              <i className="bi bi-cart display-4 d-block mb-2"></i>Заказов нет
            </div>
          ) : (
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Номер</th>
                  <th>Заявка</th>
                  <th>Поставщик</th>
                  <th className="text-center">Статус</th>
                  <th>Дата заказа</th>
                  <th>Ожид. доставка</th>
                  <th className="text-end pe-3">Сумма, ₽</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map(o => (
                  <tr key={o.id} className={o.is_overdue ? 'table-warning' : ''}>
                    <td className="ps-3">
                      <Link to={`/orders/${o.id}`} className="fw-semibold text-decoration-none">
                        {o.order_number}
                      </Link>
                      {o.is_overdue && <span className="badge bg-warning text-dark ms-1">Просроч.</span>}
                    </td>
                    <td className="small">
                      <Link to={`/requests/${o.request}`} className="text-decoration-none">{o.request_number}</Link>
                    </td>
                    <td className="small">{o.supplier_name}</td>
                    <td className="text-center">
                      <span className={`badge bg-${STATUS_COLORS[o.status]}`}>{STATUS_LABELS[o.status]}</span>
                    </td>
                    <td className="small">{o.order_date}</td>
                    <td className="small">{o.expected_delivery_date || '—'}</td>
                    <td className="text-end pe-3 small">{Number(o.total_amount).toLocaleString('ru')}</td>
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
