import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../context/AuthContext.jsx'

const STATUS_LABELS = {
  draft: 'Черновик', submitted: 'На рассмотрении', approved: 'Утверждена',
  rejected: 'Отклонена', ordered: 'Размещён заказ', completed: 'Исполнена',
}
const STATUS_COLORS = {
  draft: 'secondary', submitted: 'primary', approved: 'success',
  rejected: 'danger', ordered: 'info', completed: 'dark',
}

export default function Dashboard() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [requests, setRequests] = useState([])

  useEffect(() => {
    if (!user) return
    if (['analyst', 'manager', 'admin', 'purchaser'].includes(user.role)) {
      axios.get('/api/analytics/dashboard/').then(r => setData(r.data)).catch(() => {})
    }
    axios.get('/api/requests/?page_size=10').then(r => setRequests(r.data.results || [])).catch(() => {})
  }, [user])

  return (
    <div>
      <h1 className="page-title mb-4">
        <i className="bi bi-speedometer2 me-2"></i>
        Добро пожаловать, {user?.full_name || user?.username}!
      </h1>

      {/* Stats for analyst/manager/admin */}
      {data && (
        <div className="row g-3 mb-4">
          {[
            { label: 'Заявки', val: data.total_requests, icon: 'file-earmark-text', color: '#1a237e', border: '#1a237e' },
            { label: 'Заказы', val: data.total_orders, icon: 'cart3', color: '#2e7d32', border: '#2e7d32' },
            { label: 'Поставщиков', val: data.total_suppliers, icon: 'building', color: '#e65100', border: '#e65100' },
            { label: 'Ценовых предложений', val: data.total_quotes, icon: 'currency-dollar', color: '#6a1b9a', border: '#6a1b9a' },
          ].map(({ label, val, icon, color, border }) => (
            <div className="col-6 col-lg-3" key={label}>
              <div className="card stat-card h-100" style={{ borderLeftColor: border }}>
                <div className="card-body d-flex align-items-center gap-3">
                  <div style={{ fontSize: '2rem', color }}><i className={`bi bi-${icon}`}></i></div>
                  <div>
                    <div style={{ fontSize: '1.6rem', fontWeight: 700, color }}>{val}</div>
                    <div className="text-muted small">{label}</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Status pie data */}
      {data?.status_data && (
        <div className="row g-3 mb-4">
          <div className="col-lg-6">
            <div className="card h-100">
              <div className="card-header bg-white fw-semibold">
                <i className="bi bi-pie-chart me-1 text-primary"></i> Заявки по статусам
              </div>
              <div className="card-body">
                {Object.entries(data.status_data).map(([label, count]) => (
                  <div key={label} className="mb-2">
                    <div className="d-flex justify-content-between small mb-1">
                      <span>{label}</span><span className="fw-semibold">{count}</span>
                    </div>
                    <div className="progress" style={{ height: 6 }}>
                      <div className="progress-bar bg-primary" style={{
                        width: `${data.total_requests ? (count / data.total_requests) * 100 : 0}%`
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {data.shortage_stocks?.length > 0 && (
            <div className="col-lg-6">
              <div className="card h-100">
                <div className="card-header bg-white fw-semibold text-danger">
                  <i className="bi bi-exclamation-triangle me-1"></i> Позиции ниже минимума
                </div>
                <div className="card-body p-0">
                  <table className="table table-sm table-hover mb-0">
                    <tbody>
                      {data.shortage_stocks.slice(0, 7).map(s => (
                        <tr key={s.id}>
                          <td className="ps-3 small">{s.material_code}</td>
                          <td className="small">{s.material_name?.substring(0, 35)}…</td>
                          <td className="text-end pe-3 text-danger small">
                            {parseFloat(s.qty_available).toFixed(0)} / {parseFloat(s.material_min_stock).toFixed(0)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent requests */}
      <div className="card">
        <div className="card-header bg-white d-flex justify-content-between align-items-center">
          <span className="fw-semibold"><i className="bi bi-clock-history me-1 text-primary"></i> Последние заявки</span>
          <Link to="/requests" className="btn btn-sm btn-outline-primary">Все заявки</Link>
        </div>
        <div className="card-body p-0">
          {requests.length === 0 ? (
            <div className="text-center text-muted py-4 small">Заявок пока нет</div>
          ) : (
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Номер</th>
                  <th>Подразделение</th>
                  <th>Тип</th>
                  <th>Статус</th>
                  <th>Дата нужды</th>
                </tr>
              </thead>
              <tbody>
                {requests.map(r => (
                  <tr key={r.id}>
                    <td className="ps-3">
                      <Link to={`/requests/${r.id}`} className="fw-semibold text-decoration-none">
                        {r.request_number}
                      </Link>
                    </td>
                    <td className="small text-muted">{r.department}</td>
                    <td>
                      <span className={`badge bg-${r.criticality === 'emergency' ? 'danger' : 'secondary'}`}>
                        {r.criticality === 'emergency' ? 'Аварийная' : 'Плановая'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge bg-${STATUS_COLORS[r.status] || 'secondary'}`}>
                        {STATUS_LABELS[r.status] || r.status}
                      </span>
                    </td>
                    <td className="small">{r.need_date}</td>
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
