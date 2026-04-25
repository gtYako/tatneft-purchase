import { useEffect, useState } from 'react'
import axios from 'axios'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const PIE_COLORS = ['#6c757d', '#0d6efd', '#198754', '#dc3545', '#0dcaf0', '#212529']

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/analytics/dashboard/').then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>
  if (!data) return <div className="alert alert-danger">Нет данных</div>

  const pieData = Object.entries(data.status_data || {}).map(([name, value]) => ({ name, value }))
  const topMatsData = (data.top_materials || []).map(m => ({
    name: m.code || m.name?.substring(0, 15),
    КП: m.q_count,
  }))

  return (
    <div>
      <h1 className="page-title mb-4"><i className="bi bi-bar-chart me-2"></i>Аналитика закупок</h1>

      {/* KPI */}
      <div className="row g-3 mb-4">
        {[
          { label: 'Всего заявок', val: data.total_requests, icon: 'file-earmark-text', color: '#1a237e' },
          { label: 'Заказов', val: data.total_orders, icon: 'cart3', color: '#2e7d32' },
          { label: 'Поставщиков', val: data.total_suppliers, icon: 'building', color: '#e65100' },
          { label: 'Ценовых предложений', val: data.total_quotes, icon: 'currency-dollar', color: '#6a1b9a' },
        ].map(({ label, val, icon, color }) => (
          <div className="col-6 col-lg-3" key={label}>
            <div className="card stat-card" style={{ borderLeftColor: color }}>
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

      <div className="row g-3 mb-4">
        {/* Status pie */}
        <div className="col-lg-5">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">
              <i className="bi bi-pie-chart me-1 text-primary"></i> Заявки по статусам
            </div>
            <div className="card-body d-flex flex-column align-items-center">
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={90}
                    dataKey="value" nameKey="name" label={({ name, value }) => value > 0 ? `${value}` : ''}>
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Top materials by quotes */}
        <div className="col-lg-7">
          <div className="card h-100">
            <div className="card-header bg-white fw-semibold">
              <i className="bi bi-bar-chart me-1 text-success"></i> Топ материалов по числу КП
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={topMatsData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip />
                  <Bar dataKey="КП" fill="#1a237e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Low stock */}
      {data.shortage_stocks?.length > 0 && (
        <div className="card mb-4">
          <div className="card-header bg-white fw-semibold text-danger">
            <i className="bi bi-exclamation-triangle me-1"></i> Позиции ниже минимального запаса
          </div>
          <div className="card-body p-0">
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr><th className="ps-3">Код</th><th>Материал</th><th>Место хранения</th><th className="text-end">Доступно</th><th className="text-end pe-3">Минимум</th></tr>
              </thead>
              <tbody>
                {data.shortage_stocks.map(s => (
                  <tr key={s.id} className="table-danger">
                    <td className="ps-3"><code className="text-primary">{s.material_code}</code></td>
                    <td className="small">{s.material_name?.substring(0, 50)}</td>
                    <td className="small text-muted">{s.location}</td>
                    <td className="text-end small fw-semibold">{parseFloat(s.qty_available).toFixed(1)} {s.material_unit}</td>
                    <td className="text-end pe-3 small">{parseFloat(s.material_min_stock).toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recent quotes */}
      <div className="card">
        <div className="card-header bg-white fw-semibold">
          <i className="bi bi-clock-history me-1 text-primary"></i> Последние ценовые предложения
        </div>
        <div className="card-body p-0">
          <table className="table table-sm table-hover mb-0">
            <thead className="table-light">
              <tr><th className="ps-3">Материал</th><th>Поставщик</th><th className="text-end">Цена, ₽</th><th>Дата</th></tr>
            </thead>
            <tbody>
              {data.recent_quotes?.map(q => (
                <tr key={q.id}>
                  <td className="ps-3 small"><code>{q.material_code}</code> {q.material_name?.substring(0, 40)}</td>
                  <td className="small">{q.supplier_name}</td>
                  <td className="text-end small">{Number(q.price).toLocaleString('ru')}</td>
                  <td className="small">{q.quote_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
