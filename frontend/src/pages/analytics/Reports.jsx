import { useEffect, useState } from 'react'
import axios from 'axios'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'

const PIE_COLORS = ['#6c757d', '#0d6efd', '#198754', '#dc3545', '#0dcaf0']

export default function Reports() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/analytics/reports/').then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>
  if (!data) return <div className="alert alert-danger">Нет данных</div>

  const monthlyData = (data.monthly_requests || []).map(m => ({
    month: m.month,
    'Заявок': m.count,
    'Сумма, тыс. ₽': m.total ? Math.round(m.total / 1000) : 0,
  }))

  const orderStatusData = Object.entries(data.orders_by_status || {}).map(([name, value]) => ({ name, value }))

  const supplierData = (data.top_suppliers || []).map(s => ({
    name: s.name?.substring(0, 20),
    'Заказов': s.orders_count,
    'Рейтинг': s.rating,
  }))

  return (
    <div>
      <h1 className="page-title mb-4"><i className="bi bi-file-earmark-bar-graph me-2"></i>Сводные отчёты</h1>

      {/* Summary KPIs */}
      <div className="row g-3 mb-4">
        {[
          { label: 'Всего заявок', val: data.total_requests, color: '#1a237e', icon: 'file-earmark-text' },
          { label: 'Утверждённых', val: data.approved_requests, color: '#2e7d32', icon: 'check-circle' },
          { label: 'Заказов всего', val: data.total_orders, color: '#e65100', icon: 'cart3' },
          { label: 'Доставлено', val: data.delivered_orders, color: '#00838f', icon: 'truck' },
        ].map(({ label, val, color, icon }) => (
          <div className="col-6 col-lg-3" key={label}>
            <div className="card stat-card" style={{ borderLeftColor: color }}>
              <div className="card-body d-flex align-items-center gap-3">
                <div style={{ fontSize: '2rem', color }}><i className={`bi bi-${icon}`}></i></div>
                <div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 700, color }}>{val ?? 0}</div>
                  <div className="text-muted small">{label}</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Monthly requests bar chart */}
      <div className="card mb-4">
        <div className="card-header bg-white fw-semibold">
          <i className="bi bi-bar-chart-line me-1 text-primary"></i> Заявки по месяцам
        </div>
        <div className="card-body">
          {monthlyData.length === 0 ? (
            <div className="text-center text-muted py-4">Нет данных</div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }}
                  tickFormatter={v => `${v}k`} />
                <Tooltip
                  formatter={(v, name) => name === 'Сумма, тыс. ₽' ? [`${v} тыс. ₽`, name] : [v, name]}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar yAxisId="left" dataKey="Заявок" fill="#1a237e" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="right" dataKey="Сумма, тыс. ₽" fill="#2e7d32" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="row g-3 mb-4">
        {/* Orders by status pie */}
        <div className="col-lg-5">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">
              <i className="bi bi-pie-chart me-1 text-warning"></i> Заказы по статусам
            </div>
            <div className="card-body d-flex flex-column align-items-center">
              {orderStatusData.length === 0 ? (
                <div className="text-center text-muted py-4">Нет данных</div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={orderStatusData} cx="50%" cy="50%" outerRadius={95}
                      dataKey="value" nameKey="name"
                      label={({ name, value }) => value > 0 ? `${value}` : ''}>
                      {orderStatusData.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* Top suppliers */}
        <div className="col-lg-7">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">
              <i className="bi bi-building me-1 text-success"></i> Топ поставщиков по числу заказов
            </div>
            <div className="card-body">
              {supplierData.length === 0 ? (
                <div className="text-center text-muted py-4">Нет данных</div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={supplierData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={100} />
                    <Tooltip />
                    <Bar dataKey="Заказов" fill="#e65100" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Supplier table */}
      {data.top_suppliers?.length > 0 && (
        <div className="card">
          <div className="card-header bg-white fw-semibold">Детализация по поставщикам</div>
          <div className="card-body p-0">
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Поставщик</th>
                  <th className="text-center">Рейтинг</th>
                  <th className="text-center">Надёжность</th>
                  <th className="text-center">Заказов</th>
                  <th className="text-end pe-3">КП</th>
                </tr>
              </thead>
              <tbody>
                {data.top_suppliers.map(s => (
                  <tr key={s.id}>
                    <td className="ps-3 fw-semibold small">{s.name}</td>
                    <td className="text-center small">
                      <span className={`badge bg-${s.rating >= 8 ? 'success' : s.rating >= 5 ? 'warning' : 'danger'}`}>
                        {s.rating}/10
                      </span>
                    </td>
                    <td className="text-center small">{s.delivery_reliability}%</td>
                    <td className="text-center small">{s.orders_count}</td>
                    <td className="text-end pe-3 small">{s.quotes_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
