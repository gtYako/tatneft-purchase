import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function QuoteSelect() {
  const { itemPk } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedQuoteId, setSelectedQuoteId] = useState('')
  const [justification, setJustification] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    axios.get(`/api/items/${itemPk}/analyse/`)
      .then(r => setData(r.data))
      .finally(() => setLoading(false))
  }, [itemPk])

  const handleSubmit = async e => {
    e.preventDefault()
    if (!selectedQuoteId) { setMsg('Выберите предложение'); return }
    setSaving(true)
    try {
      await axios.post(`/api/items/${itemPk}/select-quote/`, {
        quote_id: selectedQuoteId, justification,
      })
      navigate(`/requests/${data.request_id}`)
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Ошибка')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="spinner-center"><div className="spinner-border text-primary" /></div>
  if (!data) return <div className="alert alert-danger">Данные не найдены</div>

  const { item, comparisons } = data

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-4">
        <Link to={`/requests/${data.request_id}`} className="btn btn-outline-secondary btn-sm">
          <i className="bi bi-arrow-left"></i>
        </Link>
        <div>
          <h1 className="page-title mb-0">Выбор ценового предложения</h1>
          <small className="text-muted">Заявка {data.request_number} · {item.material_code} — {item.material_name}</small>
        </div>
      </div>

      <div className="alert alert-info py-2 small mb-3">
        <i className="bi bi-info-circle me-1"></i>
        К закупке: <strong>{parseFloat(item.qty_to_purchase).toFixed(1)} {item.material_unit}</strong>.
        Оценка поставщиков рассчитана по критериям: цена, срок поставки, надёжность.
      </div>

      {msg && <div className="alert alert-danger py-2">{msg}</div>}

      {comparisons.length === 0 ? (
        <div className="alert alert-warning">
          <i className="bi bi-exclamation-triangle me-1"></i>
          Нет ценовых предложений для данного материала. Добавьте КП в карточке материала.
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="row g-3 mb-3">
            {comparisons.map((c, i) => (
              <div className="col-md-6 col-lg-4" key={c.quote_id}>
                <div className={`card h-100 ${c.is_recommended ? 'border-success' : ''} ${selectedQuoteId == c.quote_id ? 'border-primary shadow' : ''}`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedQuoteId(c.quote_id)}>
                  <div className="card-header d-flex justify-content-between align-items-center"
                    style={{ background: c.is_recommended ? '#e8f5e9' : '#fff' }}>
                    <div className="fw-semibold small">{c.supplier_name}</div>
                    <div className="d-flex gap-1">
                      {c.is_recommended && <span className="badge bg-success">Рекомендован</span>}
                      {c.is_selected && <span className="badge bg-primary">Выбран</span>}
                    </div>
                  </div>
                  <div className="card-body">
                    <div className="d-flex justify-content-between mb-2">
                      <span className="text-muted small">Цена за ед.</span>
                      <strong>{Number(c.price).toLocaleString('ru')} ₽</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span className="text-muted small">Итого</span>
                      <strong>{(Number(c.price) * parseFloat(item.qty_to_purchase)).toLocaleString('ru')} ₽</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span className="text-muted small">Срок поставки</span>
                      <span>{c.delivery_days} дн.</span>
                    </div>
                    <div className="d-flex justify-content-between mb-3">
                      <span className="text-muted small">Рейтинг поставщика</span>
                      <span>{c.supplier_rating}/10</span>
                    </div>
                    <div className="mb-1">
                      <div className="d-flex justify-content-between small mb-1">
                        <span>Цена</span><span className="fw-semibold">{c.price_score}%</span>
                      </div>
                      <div className="progress mb-1" style={{ height: 4 }}>
                        <div className="progress-bar bg-primary" style={{ width: `${c.price_score}%` }} />
                      </div>
                      <div className="d-flex justify-content-between small mb-1">
                        <span>Срок</span><span className="fw-semibold">{c.delivery_score}%</span>
                      </div>
                      <div className="progress mb-1" style={{ height: 4 }}>
                        <div className="progress-bar bg-info" style={{ width: `${c.delivery_score}%` }} />
                      </div>
                      <div className="d-flex justify-content-between small mb-1">
                        <span>Надёжность</span><span className="fw-semibold">{c.reliability_score}%</span>
                      </div>
                      <div className="progress" style={{ height: 4 }}>
                        <div className="progress-bar bg-success" style={{ width: `${c.reliability_score}%` }} />
                      </div>
                    </div>
                    <div className="text-center mt-3 pt-2 border-top">
                      <span style={{ fontSize: '1.2rem', fontWeight: 700, color: '#1a237e' }}>
                        {c.total_score}%
                      </span>
                      <span className="text-muted small ms-1">рейтинг</span>
                    </div>
                    <div className="mt-2">
                      <div className="form-check">
                        <input className="form-check-input" type="radio" name="quote"
                          id={`q-${c.quote_id}`} value={c.quote_id}
                          checked={selectedQuoteId == c.quote_id}
                          onChange={() => setSelectedQuoteId(c.quote_id)} />
                        <label className="form-check-label small fw-semibold" htmlFor={`q-${c.quote_id}`}>
                          Выбрать этого поставщика
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="card mb-3">
            <div className="card-body">
              <label className="form-label fw-semibold small">
                Обоснование выбора поставщика <span className="text-danger">*</span>
              </label>
              <textarea className="form-control" rows={3} required value={justification}
                placeholder="Укажите причину выбора данного поставщика..."
                onChange={e => setJustification(e.target.value)} />
            </div>
          </div>

          <div className="d-flex gap-2">
            <button type="submit" className="btn btn-primary" disabled={saving || !selectedQuoteId}>
              {saving
                ? <><span className="spinner-border spinner-border-sm me-2" />Сохранение...</>
                : <><i className="bi bi-check-circle me-1"></i>Подтвердить выбор поставщика</>
              }
            </button>
            <Link to={`/requests/${data.request_id}`} className="btn btn-outline-secondary">
              <i className="bi bi-x-lg me-1"></i>Отмена
            </Link>
          </div>
        </form>
      )}
    </div>
  )
}
