import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

export default function ShortageReport() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/analytics/shortage/').then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  return (
    <div>
      <h1 className="page-title mb-4"><i className="bi bi-exclamation-triangle me-2"></i>Отчёт о дефиците</h1>

      <div className="row g-3 mb-4">
        <div className="col-md-6 col-lg-4">
          <div className="card stat-card" style={{ borderLeftColor: '#dc3545' }}>
            <div className="card-body">
              <div className="text-muted small">Позиций ниже минимума</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#dc3545' }}>
                {data?.low_stocks?.length || 0}
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-4">
          <div className="card stat-card" style={{ borderLeftColor: '#fd7e14' }}>
            <div className="card-body">
              <div className="text-muted small">Позиций к дозакупке</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#fd7e14' }}>
                {data?.shortage_items?.length || 0}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Shortage from requests */}
      <div className="card mb-4">
        <div className="card-header bg-white fw-semibold text-warning">
          <i className="bi bi-cart-x me-1"></i> Позиции к закупке (по активным заявкам)
        </div>
        <div className="card-body p-0">
          {!data?.shortage_items?.length ? (
            <div className="text-center text-muted py-4 small">Нет позиций к закупке</div>
          ) : (
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Заявка</th>
                  <th>Материал</th>
                  <th className="text-center">Тип</th>
                  <th className="text-center">Запрошено</th>
                  <th className="text-center">На складе</th>
                  <th className="text-center">К закупке</th>
                  <th className="text-end pe-3">Сумма, ₽</th>
                </tr>
              </thead>
              <tbody>
                {data.shortage_items.map(item => (
                  <tr key={item.id}
                    className={item.request?.criticality === 'emergency' ? 'table-danger' : ''}>
                    <td className="ps-3 small">
                      {item.request && (
                        <Link to={`/requests/${item.request}`} className="fw-semibold text-decoration-none">
                          {item.request_number || '—'}
                        </Link>
                      )}
                    </td>
                    <td className="small">
                      <code className="text-primary">{item.material_code}</code>
                      <span className="ms-1 text-muted">{item.material_name?.substring(0, 40)}</span>
                    </td>
                    <td className="text-center">
                      <span className="badge bg-secondary">Плановая</span>
                    </td>
                    <td className="text-center small">{parseFloat(item.qty_requested).toFixed(1)} {item.material_unit}</td>
                    <td className="text-center small text-success">{parseFloat(item.qty_available_at_warehouse).toFixed(1)}</td>
                    <td className="text-center small fw-semibold text-danger">{parseFloat(item.qty_to_purchase).toFixed(1)}</td>
                    <td className="text-end pe-3 small">
                      {item.line_total ? Number(item.line_total).toLocaleString('ru') : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Low stock */}
      <div className="card">
        <div className="card-header bg-white fw-semibold text-danger">
          <i className="bi bi-exclamation-triangle-fill me-1"></i> Позиции ниже минимального запаса
        </div>
        <div className="card-body p-0">
          {!data?.low_stocks?.length ? (
            <div className="text-center text-muted py-4 small">Все позиции в норме</div>
          ) : (
            <table className="table table-sm table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="ps-3">Код</th>
                  <th>Материал</th>
                  <th>Место хранения</th>
                  <th className="text-end">На складе</th>
                  <th className="text-end">Доступно</th>
                  <th className="text-end pe-3">Минимум</th>
                </tr>
              </thead>
              <tbody>
                {data.low_stocks.map(s => (
                  <tr key={s.id} className="table-danger">
                    <td className="ps-3"><code className="text-primary small">{s.material_code}</code></td>
                    <td className="small">
                      <Link to={`/catalog/${s.material}`} className="text-decoration-none fw-semibold">
                        {s.material_name?.substring(0, 45)}
                      </Link>
                    </td>
                    <td className="small text-muted">{s.location}</td>
                    <td className="text-end small">{parseFloat(s.qty_on_hand).toFixed(1)} {s.material_unit}</td>
                    <td className="text-end small fw-semibold">{parseFloat(s.qty_available).toFixed(1)}</td>
                    <td className="text-end pe-3 small">{parseFloat(s.material_min_stock).toFixed(1)}</td>
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
