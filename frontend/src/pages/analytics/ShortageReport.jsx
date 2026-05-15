import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import * as XLSX from 'xlsx'

const num = value => Number.parseFloat(value || 0)
const money = value => value ? Number(value).toLocaleString('ru-RU') : '—'

export default function ShortageReport() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/analytics/shortage/').then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  const exportExcel = () => {
    if (!data) return
    const shortageItems = data.shortage_items || []
    const lowStocks = data.low_stocks || []
    const wb = XLSX.utils.book_new()

    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([
      ['Отчёт о дефиците'],
      ['Дата формирования', new Date().toLocaleString('ru-RU')],
      ['Позиций ниже минимума', lowStocks.length],
      ['Позиций к дозакупке', shortageItems.length],
    ]), 'Сводка')

    const purchaseRows = shortageItems.map(item => ({
      'Заявка': item.request_number || '',
      'Материал': `${item.material_code || ''} ${item.material_name || ''}`.trim(),
      'Тип': item.request?.criticality === 'emergency' ? 'Аварийная' : 'Плановая',
      'Запрошено': num(item.qty_requested),
      'Ед.': item.material_unit || '',
      'На складе': num(item.qty_available_at_warehouse),
      'К закупке': num(item.qty_to_purchase),
      'Сумма, ₽': item.line_total ? Number(item.line_total) : null,
    }))
    const purchaseSheet = XLSX.utils.json_to_sheet(purchaseRows)
    purchaseSheet['!cols'] = [
      { wch: 16 }, { wch: 58 }, { wch: 14 }, { wch: 12 },
      { wch: 8 }, { wch: 12 }, { wch: 12 }, { wch: 14 },
    ]
    XLSX.utils.book_append_sheet(wb, purchaseSheet, 'К закупке')

    const lowStockRows = lowStocks.map(s => ({
      'Код': s.material_code || '',
      'Материал': s.material_name || '',
      'Место хранения': s.location || '',
      'На складе': num(s.qty_on_hand),
      'Ед.': s.material_unit || '',
      'Доступно': num(s.qty_available),
      'Минимум': num(s.material_min_stock),
    }))
    const lowStockSheet = XLSX.utils.json_to_sheet(lowStockRows)
    lowStockSheet['!cols'] = [
      { wch: 14 }, { wch: 58 }, { wch: 42 }, { wch: 12 },
      { wch: 8 }, { wch: 12 }, { wch: 12 },
    ]
    XLSX.utils.book_append_sheet(wb, lowStockSheet, 'Ниже минимума')

    XLSX.writeFile(wb, `shortage-report-${new Date().toISOString().slice(0, 10)}.xlsx`)
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>

  return (
    <div>
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-4">
        <h1 className="page-title mb-0"><i className="bi bi-exclamation-triangle me-2"></i>Отчёт о дефиците</h1>
        <button className="btn btn-outline-success" onClick={exportExcel} disabled={!data}>
          <i className="bi bi-file-earmark-excel me-1"></i>Выгрузить Excel
        </button>
      </div>

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
                      <span className="badge bg-secondary">
                        {item.request?.criticality === 'emergency' ? 'Аварийная' : 'Плановая'}
                      </span>
                    </td>
                    <td className="text-center small">{num(item.qty_requested).toFixed(1)} {item.material_unit}</td>
                    <td className="text-center small text-success">{num(item.qty_available_at_warehouse).toFixed(1)}</td>
                    <td className="text-center small fw-semibold text-danger">{num(item.qty_to_purchase).toFixed(1)}</td>
                    <td className="text-end pe-3 small">{money(item.line_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

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
                    <td className="text-end small">{num(s.qty_on_hand).toFixed(1)} {s.material_unit}</td>
                    <td className="text-end small fw-semibold">{num(s.qty_available).toFixed(1)}</td>
                    <td className="text-end pe-3 small">{num(s.material_min_stock).toFixed(1)}</td>
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
